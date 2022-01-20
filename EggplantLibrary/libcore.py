from datetime import datetime
import inspect
import xmlrpc.client
import os

import robot.api.logger as log
from robot.libraries.BuiltIn import BuiltIn

draw_rects_on_screenshots = True
try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError as e:
    log.warn(f"Pillow not found, drawing rectangles on screenshots is disabled: {e}."    
    " Install using: 'pip install Pillow'.")
    draw_rects_on_screenshots = False

from . import utils


class EggplantExecutionException(Exception):
    """
    Special Exception we use in case of errors which occur inside the "RunWithNewResults" execution
    """


class EggplantLibDynamicCore:

    def __init__(self, suite='', host='', port='', scripts_dir=''):
        """
        Each library import is bound to a single *eggPlant test suite* and to an *eggPlant instance running in the eggDrive mode*.
        
        No actual XML RPC connection is established during the import, so there is no must to start eggPlant in advance.   
        
        The library needs a file access to the ``.suite`` folder in order to build the list of keywords (i.e. eggPlant ``.script`` files)
        and get their arguments and documentation.
        
        == Import examples ==
        | Library | EggplantLibrary | suite=E:/eggPlantScripts/SuiteOne.suite | host=http://127.0.0.1 | port=5400 |
        | Library | EggplantLibrary | # Import without parameters needs `EggplantLib.config` in the library package dir |

        == Import Parameters ==

        *Each of import parameter is optional and may stay unset during library import.*   

        In this case library looks for it's value in the *config file* (`EggplantLib.config`) in the library package dir.
        If no value found in the config file (or no file exists), the default value is used.
        
        === suite ===
        Path to the eggPlant `.suite` file.
        - The default value is a first `.suite` file in the library folder.
        - You can also select another eggPlant suite for actual execution using `Open Session` and `Close Session` keywords.   
        - If eggPlant runs on a remote server,input here a path from the library host, not relative to the server! And it must be reachable.   

        === host ===
        Host name or IP address of the eggPlant instance running in the eggDrive mode (i.e. XMLRPC server).  
        - The default value is `http://127.0.0.1`.   
        - You can also select another host name for actual execution using `Set eggDrive Connection` keyword.  
        - *Currently tested on localhost only!* It will be a miracle if it works just like this with a remote eggPlant server.

        === port ===
        Port of the eggPlant instance running in the eggDrive mode (i.e. XMLRPC server). 
        - The default value is `5400`.
        - You can also select another port for actual execution using `Set eggDrive Connection` keyword.

        === scripts_dir ===
        Folder inside the eggPlant Suite, where all scripts are located.
        - The default value is `Scripts`.
        - Subfolders are supported.
        """

        # Get all params from the library import string first.
        # If some of the empty, try to look in a config file.
        # If nothing found, use default values
        params = {'host': 'http://127.0.0.1', 'port': '5400', 'scripts_dir': 'Scripts', 'suite': suite}  # defaults
        for p_key in params:
            if locals()[p_key] == '':  # if parameter value passed to the lib constructor is empty..
                value_from_config = self.read_from_config(p_key)
                if value_from_config != '':
                    params[p_key] = value_from_config
            else:
                params[p_key] = locals()[p_key]  # otherwise set the passed argument value

        uri = params['host'] + ":" + params['port']
        self.eggplant_server = xmlrpc.client.ServerProxy(uri)

        # Now check if the eggPlant suite path is set
        self.eggplant_suite = params['suite']
        this_dir = os.path.abspath(os.path.dirname(__file__))

        # if suite path still not set, use first ".suite" dir in the library folder
        if self.eggplant_suite == '':
            for name in os.listdir(this_dir):
                if name.endswith(".suite"):
                    self.eggplant_suite = os.path.abspath(os.path.join(this_dir, name))
                    break
        # otherwise suite path is set, but make sure it's absolute
        else:
            if not os.path.isabs(self.eggplant_suite):
                self.eggplant_suite = os.path.abspath(os.path.join(this_dir, self.eggplant_suite))

        # TODO: if the eggPlant runs on a remote server, the test suite dir will be remote as well! How access it?

        # the default directory with keywords (=eggPlant scripts) is 'Scripts' inside the eggPlant test suite
        self.keywords_dir = os.path.join(self.eggplant_suite, params['scripts_dir'])

        # For video recording
        self.current_movie_path = None

        self.eggplant_version_checked = False

    # ---------- RobotFramework API implementation ------------
    def get_keyword_names(self):
        """
        Returns all available eggPlant keywords.
        The static keywords (methods of this library class, decorated with @keyword) are collected via reflection.
        The list of eggPlant keywords is build from '.script' files, collected in the 'Scripts' folder
        in the eggPlant Suite and all subfolders.

        :return List of all collected keywords - including static keywords and eggPlant scripts
        """
        keywords = []

        # get static keywords first - from this library class only
        for name in dir(self):
            if self.get_static_keyword(name):
                keywords.append(name)

        # now fetch eggPlant scripts and add them as keywords - from all subfolders
        self.get_scripts_from_folder(self.keywords_dir, keywords)

        log.debug("Found keywords: {}".format(keywords))

        return keywords

    def run_keyword(self, name, args):
        """
        Runs the requested keyword with the specified arguments.
        For static keyword just the Python function is called using reflection.
        For eggPlant scripts the eggDrive command is built using 'RunWithNewResults' and sent to the eggPlant server,
            like 'RunWithNewResults "scriptName" arg1, "arg2", arg3,'.
        If a subscrtipt from a subfolder is called (e.g. 'subfolder.script'), the dots (.) are replaced with slashes (/)

        String arguments with spaces inside will be surrounded with quotes (") automatically.
        eggPlant list syntax is supported - like 'script (1, "val2", "3", val4)'

        :return The 'ReturnValue' from the 'Result' value of the XML RPC response for eggPlant scripts
                or the keyword return value in case of static keywords.
        """

        # consider the requested keyword as static first
        _keyword = self.get_static_keyword(name)
        if _keyword:
            return _keyword(*args)

        else:  # otherwise it's an eggPlant script
            command = name
            if "." in command:  # if it's a script in a subfolder
                command = command.replace(".", "/")
            try:
                result = self.run_with_new_results(command, *args)
                return result

            # Failure in parsed result string
            except EggplantExecutionException as e:
                search_rect = self.log_ocr_debug_info(str(e))
                screenshot = self.take_screenshot(highlight_rectangle=search_rect, error_if_no_sut=False)
                if self.current_movie_path:
                    self.log_embedded_video(self.current_movie_path, screenshot)
                elif screenshot:
                    self.log_embedded_image(screenshot)

                raise Exception(f"{name}: {e}")

            # common eggDrive error
            except xmlrpc.client.Fault as e:
                log.error("{}: XMLRPC execution failure! Fault code:{}. Fault string: {}".format(name, e.faultCode,
                                                                                                 e.faultString))
                screenshot = self.take_screenshot(error_if_no_sut=False)
                if self.current_movie_path:
                    self.log_embedded_video(self.current_movie_path, screenshot)
                else:
                    self.log_embedded_image(screenshot)
                raise e

            except Exception as e:
                log.error("Unknown error occurred! {}".format(e))
                # assuming we don't need a screenshot if it's not an egPlant exception
                # self.screenshot()
                raise e

    # def get_keyword_tags(self, name):
    # we'd need this function if keyword tags would be fetched otherwise as via last docs line.
    # See http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#getting-keyword-tags

    def get_keyword_documentation(self, name):
        """
        Fetches the keyword documentation.
        For static keywords it takes a standard Python doc (comment below method declaration).
        For eggPlant scripts the top comment block of a script file is returned (without comment start/end characters).
        :param name: keyword name
        """

        result = None
        static_keyword = self.get_static_keyword(name)
        if static_keyword:
            result = inspect.getdoc(static_keyword)
        else:
            if name in ['__init__', '__intro__']:  # standard RF library specification, needed e.g. in RED
                method = getattr(self, name, False)
                if method:
                    result = inspect.getdoc(method)
            else:
                result = self.get_top_comments(name)

        return result

    def get_keyword_arguments(self, name):
        """
        Returns function signature - which arguments it can take.
        Allows RobotFramework to check the arguments accuracy in calling keywords even before trying to run them.
        Also quite useful for code completion in IDE plugins.
        :param name: keyword name to fetch arguments for
        :return: list of arguments
        """

        result_list = []

        # consider the requested keyword as static first
        static_keyword = self.get_static_keyword(name)
        if static_keyword:
            fullargs = inspect.getfullargspec(static_keyword)
            args = fullargs[0]
            varargs = fullargs[1]
            kwargs = fullargs[2]
            defaults = fullargs[3]
            kwonlyargs = fullargs[4]
            kwonlydefaults = fullargs[5]

            # add to usual positional args possible defaults
            if defaults is not None:
                i = len(args) - 1
                for default in reversed(defaults):
                    args[i] += "=" + str(default)
                    i -= 1
            # remove "self" from the args list manually
            if args[0] == "self":
                del (args[0])
            result_list = args

            # named args if available
            if varargs is not None:
                result_list.append("*" + varargs)

            # add defaults to named only arguments
            if kwonlydefaults is not None:
                i = len(kwonlyargs) - 1
                for default in reversed(kwonlydefaults):
                    kwonlyargs[i] += "=" + str(default)
                    i -= 1
                result_list.append(kwonlyargs)

            # free argument assignment if available
            if kwargs is not None:
                result_list.append("**" + kwargs)

        else:  # otherwise it's an eggPlant script
            log.debug("Reading arguments from eggPlant script file: {}".format(name))

            with open(self.get_script_file_path(name), encoding="utf8") as f:
                # look for a line with params, it must be at the file top, but might appear after comments
                params_str_start = "params "

                # we don't want to scan all scripts to the very bottom, if there are no params at all!
                # params can be preceded only by comments and empty lines
                # so we skip all top empty lines and expect params at the first line after the comments - otherwise exit
                comment_lines_length = len(self.get_top_comments(name).splitlines())
                line_counter = 0

                for line in f:
                    log.debug("Line: {}".format(line))

                    stripped_line = utils.remove_unreadable_characters_at_start(line)
                    if stripped_line == "":
                        continue  # skip top empty lines

                    line_counter += 1
                    if str.lower(stripped_line).startswith(params_str_start):  # look for "params " case insensitive
                        # found
                        args = []
                        split = stripped_line[len(params_str_start):].split(',')
                        for item in split:
                            arg_string = str(item).strip()
                            argument_tuple = (arg_string,)
                            default_value_separator = ":"
                            if default_value_separator in arg_string:  # default value available
                                arg_name = arg_string.split(default_value_separator)[0]
                                arg_default_value = arg_string.split(default_value_separator)[1]
                                # try to convert the default value to one of supported data types
                                arg_default_value = utils.convert_to_num_bool_or_string(arg_default_value)
                                # so it's a string - remove possible double quotes
                                if isinstance(arg_default_value, str):
                                    arg_default_value = arg_default_value.replace('"', '')
                                argument_tuple = (arg_name, arg_default_value)
                            args.append(argument_tuple)
                        result_list = args
                        break

                    if line_counter > comment_lines_length + 1:
                        #  +1 because of possible standalone comment closing bracket in the last line
                        break

        return result_list

    def get_keyword_source(self, name):
        result = None
        static_keyword = self.get_static_keyword(name)
        if static_keyword:
            result_path = os.path.abspath(inspect.getsourcefile(static_keyword))
            result_line = inspect.getsourcelines(static_keyword)[1]
            result = f"{result_path}:{result_line}"
        else:
            if name in ['__init__', '__intro__']:  # standard RF library specification, needed e.g. in RED
                method = getattr(self, name, False)
                if method:
                    result = os.path.abspath(inspect.getsourcefile(method))
            else:
                result = self.get_script_file_path(name)

        return result

    # ---------- Helper methods ---------------------------------
    def run_with_new_results(self, script, *args):
        """
        Builds an eggPlant command using 'RunWithNewResults' from the script and the arguments and executes it.
        :param script: the script or command to be run
        :param args: arguments. String arguments with spaces inside will be surrounded with quotes (") automatically.
        eggPlant list syntax is supported - like 'script (1, "val2", "3", val4)'
        :return: the execution result
        """

        command = "RunWithNewResults \"{}\",".format(script)
        log.debug("Now add parameters to the command string")
        for arg in args:
            log.debug("Processing argument: {}".format(arg))
            arg_f = arg

            if isinstance(arg_f, str):  # if the parameter is a string, it might need quotes..
                # convert all new line and return characters to eggPlant format
                arg_f = arg_f.replace("\n", "\" & return & \"")
                arg_f = arg_f.replace("\r", "\" & return & \"")

                if not (arg_f.startswith("(") and arg_f.endswith(")")):  # lists don't need quotes
                    if not (arg_f.startswith("\"") and arg_f.endswith("\"")):  # no quotes for already quoted string
                        arg_f = "\"" + format(arg_f) + "\""

            if isinstance(arg, list):   # eggPlant doesn't understand single quotes (') around list values
                arg_f = utils.single_quote_to_double(arg)
            log.debug("Formatted argument: {}".format(arg_f))
            command = "{} {},".format(command, arg_f)

        result = self.execute(command, parse_result=True)
        return utils.auto_convert(
            result)  # The result is always a string so we should try to convert it first

    def execute(self, command, parse_result=False, exception_on_failure=True):
        """
        Sends the requested command to the eggPlant server via XML RPC.
        The XML RPC response is parsed and logged.

        :param command: the eggPlant command in eggDrive format. Quotes have to be escaped.
        Examples: 'myScript arg1, arg2' or 'click \"someImage\"'.

        :param parse_result: if TRUE, the 'Result' value of the XML RPC response is parsed.
                            If the Result's child 'Status' doesn't report SUCCESS, an Exception is raised -
                            unless it's disabled in the optional parameter.

        :param exception_on_failure: works only if result parsing is enabled. If FALSE, no exception is raised
                                    in case the Result's child 'Status' doesn't report SUCCESS

        :return: If parsing the result is enabled, the 'ReturnValue' from the 'Result' value of the XML RPC response
                    is returned. Otherwise the 'Result' value of the XML RPC response is returned directly,
                    although it might be a result of a previous script.
        """
        log.info("Send command to eggPlant server: '{}'".format(command))

        returned_string = self.eggplant_server.execute(command)
        # example: {'Duration': 0.004000067711, 'Output': '28.01.19, 16:32:16\tconnect\t\tWindows_10_1:(null)\n',
        # 'Result': 'E:/screenshot.png', 'ReturnValue': ''}
        log.debug("Returned string: {}".format(returned_string))

        log.info("Execution duration: {}".format(returned_string['Duration']))

        output = returned_string['Output']
        log.info("Command output:")
        log.info(output, html=True)

        warning_flag = 'LogWarning'
        output_lines = output.split('\n')
        for line in output_lines:
            if warning_flag in line:
                warning_text = line.split(warning_flag)[1].strip()
                log.warn(warning_text)

        result_section = returned_string['Result']
        return_value = result_section
        log.debug("Execution result: {}".format(result_section))

        if parse_result:
            log.debug("Parsing the execution result...")
            # Parse the execution result, if it's not a usual string - which means the RunWithNewResults command sent
            ''' Usually looks like this:
                {'Duration': 0.578999996185,
                'ErrorMessage': 'SomeError',        # not available in case of success
                'Errors': 0.0,
                'Exceptions': 0.0,
                'LogFile': 'E:/eggPlantScripts/SuiteOne.suite/Results/getNotepadText/20190125_144557.016/LogFile.txt',
                'ReturnValue': 'JHello World',
                'RunDate': <DateTime '20190125T14:45:57' at 0x3615510>,
                'Status': 'Success',
                'Successes': 1.0,
                'Warnings': 0.0}
            '''

            eggdrive_command_duration = returned_string['Duration']
            eggplant_script_duration = result_section['Duration']
            if eggdrive_command_duration and eggplant_script_duration:
                execution_delay = float(eggdrive_command_duration) - float(eggplant_script_duration)
                log.debug(f"eggdrive execution delay: {execution_delay:.2f} seconds")
                if execution_delay > 30:
                    log.warn(f"eggdrive execution delay too high (>30 s): {execution_delay:.2f} seconds")
                    log.info("eggdrive execution delay - difference between eggdrive XML-RPC command duration "
                             "and eggPlant script duration")

            return_value = result_section['ReturnValue']
            status = result_section['Status']
            if status != "Success" and exception_on_failure:
                raise EggplantExecutionException(result_section['ErrorMessage'])

        log.info("Return value: {}".format(return_value))
        return return_value

    def get_static_keyword(self, name):
        """
        Returns the method object if a static keyword with the requested name exists in the library and None otherwise
        :param name: the method name to look for
        :return: the method object if found or False otherwise
        """
        # '@keyword' decorator required
        # the name must not start with '_'
        method = getattr(self, name, False)
        if method:
            if inspect.ismethod(method) and hasattr(method, 'robot_name'):
                return method
        return None

    def get_scripts_from_folder(self, folder, result_list=None, prefix=""):
        """
        The function goes recursively through all subfolders and adds names of ".script" files to the result list.
        The subfolder name is added as prefix following by a dot, e.g. "Subfolder.Myscript".
        If there are several sufolders in the structure, all of them are added as prefix, separated by a dot, e.g.
        "Subfolder.SubSubfolder.Myscript".

        :param folder - the root folder to start the recursive search
        :param result_list - optional, the list where new items are to append
        :param prefix - the subfolder prefix, is used in the recursion only. No need to set from outside!

        :return the list of all found ".script" items in all subfolders
        """
        if result_list is None:
            result_list = []
        for item in os.listdir(folder):
            current_prefix = prefix
            if current_prefix != "":
                current_prefix += "."
            if item.endswith(".script"):
                if not item.startswith('_'):  # don't add technical/internal scripts
                    script_name = current_prefix + str(item.split('.')[0])
                    result_list.append(script_name)
            else:
                item_path = os.path.join(folder, item)
                if os.path.isdir(item_path):
                    new_prefix = current_prefix + item
                    self.get_scripts_from_folder(item_path, result_list, new_prefix)
        return result_list

    def get_script_file_path(self, name):
        """
        Creates a real eggPlant script file path from the RobotFramewok keyword syntax.
        It replaces dots ('.') with slashes ('/') and builts a file path from the name.
        :param name: script path in RobotFramework format, without '.script' extension. Example: 'subfolder.Script'
        :return: real file path, e.g. '<eggPlantSuite>/Scripts/subfolder/Script.script'
        """
        name_with_replaced_dots = name.replace(".", "/")
        # the "." is replaced because of scripts in subfolders
        filepath = os.path.join(self.keywords_dir, name_with_replaced_dots + ".script")
        return filepath

    def get_top_comments(self, script_name):
        """
        Fetches all comments from the script file top.
        EggPlant single line and multi line comments are supported, they can also be combined.
        The comment block is considered close when a first non comment line is found.

        :param script_name: name of the eggPlant script in eggPlant format. Without '.script' extension.
        Not file path - it will be built from the script name automatically.
        Examples: 'myScript1', 'folder/subfolder/script'
        """
        line_comment_start_chars = ['//', '#', '--']
        multiline_comment_start = '(*'
        multiline_comment_end = '*)'

        log.debug("Reading top comments from eggPlant script file: {}".format(script_name))

        result = ""

        with open(self.get_script_file_path(script_name), encoding="utf8") as f:
            inside_multiline_comment = False
            for line in f:

                log.debug("Line: {}".format(line))

                stripped_line = utils.remove_unreadable_characters_at_start(line)

                if stripped_line == "":  # empty lines at file start are allowed
                    continue

                if stripped_line.startswith(multiline_comment_end):  # in case "*)" stays alone in a last line
                    result += "\n"
                    inside_multiline_comment = False
                    continue  # maybe there are furthermore comments?

                if inside_multiline_comment:
                    # maybe it's the last comment line with '*)' in the end?
                    if stripped_line.endswith(multiline_comment_end):
                        inside_multiline_comment = False
                        stripped_line = stripped_line.removesuffix(multiline_comment_end)
                    result += stripped_line + "\n"
                    continue  # maybe there are furthermore comments?

                # now check for single line comments
                single_comment_found = False
                for comment_starter in line_comment_start_chars:
                    if stripped_line.startswith(comment_starter):
                        single_comment_found = True
                        result += stripped_line.removeprefix(comment_starter) + "\n"
                        break  # exit the inner loop through single line comment start characters
                if single_comment_found:
                    continue

                # try to check the multiline comments otherwise
                if stripped_line.startswith(multiline_comment_start):
                    stripped_line = stripped_line.removeprefix(multiline_comment_start)
                    if stripped_line.endswith(multiline_comment_end):
                        stripped_line = stripped_line.removesuffix(multiline_comment_end)
                    else:
                        inside_multiline_comment = True
                    result += stripped_line + "\n"
                    continue

                result = result[:result.rfind("\n")]  # remove the last new line character
                break  # no comment chars found - means we don't need to go further
        return result

    def log_ocr_debug_info(self, exception_text):
        """
        Performs OCR (eggPlant 'readText' command) in the restricted search rectangle extracted from the error message.

        The error message should be in standard eggplant format: 'No Text Found On Screen: <TEXT> ...
        Restricted Search Rectangle ((1431,654),(1581,854))'

        If no restricted search rectangle is found in the message (means full screen is searched), no OCR is performed.

        :return Restricted search rectangle extracted from the error message or an empty string if no rectangle found
        """
        search_rect_text = 'Restricted Search Rectangle '
        ocr_text = 'TEXT:'
        search_rect = ''

        if search_rect_text in exception_text:
            search_rect = exception_text[exception_text.index(search_rect_text) + len(search_rect_text):].strip()
            if ocr_text in exception_text:
                log.info("----> Performing OCR ReadText in the restricted search rectangle: {0}.\n"
                         "For results see the command output further in the log.\n-----\n"
                         .format(search_rect))
                self.execute("log ReadText{}".format(search_rect))

        return search_rect

    def read_from_config(self, key, file_path=''):
        """
        Returns value of the requested parameter from the config file.
        No error thrown if file not found!
        """
        if file_path == '':
            dir_path = os.path.abspath(os.path.dirname(__file__))
            file_path = os.path.join(dir_path, "EggplantLib.config")

        if os.path.isfile(file_path):
            with open(file_path, encoding="utf8") as f:
                for line in f:
                    if line.startswith(key):
                        return line.split('=')[1].strip()

        return ''

    def take_screenshot(self, rectangle='', file_path='', highlight_rectangle='', error_if_no_sut=True):
        """
        Captures a SUT screen image and saves it into the specified file.
        Returns the file path (relative to the current Robot Framework Output Dir) or None if no SUT available.

        Be default the full screen is captured, otherwise according to the specified rectangle.

        _Parameters:_
            - *rectangle* - optional, a list of 2 values (top left, bottom right) in eggPlant format
            indicating a rectangle to capture.
            Each value might be a list of two coordinates, an image name or an image location.
            Examples: *(67, 33), imagelocation("OtherCorner")* or *RxLocation, RxLocation + (140,100)*.
            See the eggPlan docs for details:
            http://docs.testplant.com/ePF/SenseTalk/stk-results-reporting.htm#capturescreen-command

            - *file_path* - optional, relative to the current Robot Framework Output Dir.
            If not specified, the default name is used.

            - *error_if_no_sut* - normally an error is reported if no SUT connection available for taking a screenshot.
            However, this may be disabled.
        """

        # Check for a valid file_path and make sure the directories exist
        target_path = file_path

        if not file_path:
            target_path = "Screenshots\\Screenshot__{0}.png".format(datetime.now().strftime('%Y-%m-%d__%H_%M_%S__%f'))

        if target_path and os.path.isabs(target_path):
            raise RuntimeError("Given file_path='%s' must be relative to Robot output dir" % target_path)

        # image output file path is relative to robot framework output
        full_path = os.path.join(BuiltIn().get_variable_value("${OUTPUT DIR}"), target_path)
        if not os.path.exists(os.path.split(full_path)[0]):
            os.makedirs(os.path.split(full_path)[0])

        rectangle_string = ""
        rectangle_log_msg = "Full screen"
        if rectangle:
            rectangle_log_msg = rectangle
            rectangle_string = "Rectangle: ({})".format(rectangle)

        log.info(f"Screenshot rectangle: {rectangle_log_msg}")

        try:
            # Capture and save the image of the whole SUT screen
            self.eggplant_server.execute("CaptureScreen(Name:\"{0}\", {1})".format(full_path, rectangle_string))
            if highlight_rectangle:
                log.info(highlight_rectangle)
                self.draw_rect_on_image(full_path, highlight_rectangle)

        except xmlrpc.client.Fault as e:
            expected_error_message = "unable to capture screen: no connection available from which to capture"
            if expected_error_message in e.faultString.lower():
                log.debug(f"Error message: {e}")
                log_msg = "Unable to take screenshot - no SUT connection available"
                if error_if_no_sut:
                    raise EggplantExecutionException(log_msg)
                else:
                    log.warn(log_msg)
                    target_path = None

        return target_path

    def draw_rect_on_image(self, image_file, coordinates, color='red'):        
        log.debug("Draw a {} rectangle with coordinates {} for image {}".format(color, coordinates, image_file))
        
        if not draw_rects_on_screenshots:
            log.debug("Drawing rectangles disabled, check if Pillow is installed")
            return

        coord_str = str(coordinates)
        coord_str = coord_str.replace("(", "")
        coord_str = coord_str.replace(")", "")
        coord_str = coord_str.replace("[", "")
        coord_str = coord_str.replace("]", "")
        coord_str = coord_str.replace("'", "")
        coord_str = coord_str.replace(" ", "")
        coords = []
        for i in list(coord_str.split(',')):
            coords.append(int(i))
        log.debug(coord_str)
        log.debug(coords)

        im = Image.open(image_file)
        draw = ImageDraw.Draw(im)
        draw.rectangle(coords, outline=color, width=3)
        im.save(image_file)

    def log_embedded_image(self, image_path):
        """
        Writes a link to the image file into RF log - so that it appears directly in the HTMl with a small preview
        """
        image_name = os.path.basename(image_path)
        log.info(html=True, msg=f'Screenshot: <a href="{image_path}">{image_name}</a>'
                                f'<td></td></tr><tr><td colspan="3"><a href="{image_path}">'
                                f'<img src="{image_path}" height="350px"></a></td></tr>')

    def log_embedded_video(self, video_path, preview_image_path=None):
        """
        Writes a link to the video file into RF log - so that it appears as an embedded video player
        """
        preview = ""
        if preview_image_path:
            preview_image_name = os.path.basename(preview_image_path)
            log.info(html=True, msg=f'Screenshot: <a href="{preview_image_path}">{preview_image_name}</a>')
            preview = f'poster="{preview_image_path}"'

        video_name = os.path.basename(video_path)
        log.info(f'Video file path: <a href="{video_path}">{video_name}</a>', html=True)
        log.info(html=True, msg=f'<tr><video {preview} height="350px" controls> <source src="{video_path}"'
                                f' type="video/mp4">Browser does not support video.</video></tr>')
