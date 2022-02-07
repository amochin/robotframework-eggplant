from datetime import datetime
import os
import xmlrpc.client
import robot.api.logger as log
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

from .libcore import EggplantLibDynamicCore
from .version import VERSION, EGGPLANT_VERSION_MIN


class EggplantLibrary(EggplantLibDynamicCore):
    """
    The Eggplant Library for [https://robotframework.org|Robot Framework] allows calling
    [https://www.eggplantsoftware.com/eggplant-functional-downloads|eggPlant Functional] scripts via XML RPC
    using [http://docs.testplant.com/ePF/using/epf-about-eggdrive.htm|eggDrive].  
    It considers *eggPlant scripts as low level keywords* 
    and exposes them for usage in *high level keywords and test cases in Robot Framework*.   
    So the scripts themselves have to be created in eggPlant, not in Robot Framework.        

    The eggPlant itself should be launched in eggDrive mode from outside.

    See the [https://github.com/amochin/robotframework-eggplant|Eggplant Library homepage] for more information.
    """
    ROBOT_LIBRARY_VERSION = VERSION
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    # ---------- static keywords ------------------------------
    @keyword
    def set_eggdrive_connection(self, host='http://127.0.0.1', port='5400'):
        """
        Defines connection to running instance of eggPlant in the eggDrive mode
        (XML RPC Server).
        """
        uri = host + ":" + port
        self.eggplant_server = xmlrpc.client.ServerProxy(uri)

    @keyword
    def connect_sut(self, connection_string):
        """
        Opens a VNC or RDP connection with a SUT / makes it the active connection.

        The `connection_string` might be a name of a saved connection or
        a string of params. Examples:
        | Connect SUT | Windows10 |
        | Connect SUT | {serverID: "localhost", portNum: "10139", password: "secret"} |
        See [http://docs.testplant.com/ePF/SenseTalk/stk-sut-information-control.htm#connect-command|eggPlant docs]
        for more details.
        """
        self.execute("connect {}".format(connection_string))

    @keyword
    def disconnect_sut(self, connection_string):
        """
        Closes the specified VNC or RDP connection with a SUT.

        The `connection_string` might be a name of a saved connection or a string of params.
        See `Connect Sut` for more examples.
        """
        self.execute("disconnect {}".format(connection_string))

    @keyword
    def screenshot(self, rectangle='', file_path='', highlight_rectangle='', error_if_no_sut_connection=True):
        """
        Captures a SUT screen image, saves it into the specified file and logs in the Robot test log.
        By default the full screen is captured, otherwise according to the specified rectangle.

        The `rectangle` (optional) is a list of 2 values (top left, bottom right) in eggPlant format
            indicating a rectangle to capture.
            Each value might be a list of two coordinates, an image name or an image location.
        
        If `highlight_rectangle` is provided, an additional frame is drawn on the taken screenshot.
        The coordinates are passed as a string of four values: *x0, y0, x1, y1*

        The `file_path` (optional) is relative to the current Robot Framework Output Dir.
            If not specified, the default name is used.

        Normally an error is reported if no SUT connection available for taking a screenshot.
        This may be disabled using the `error_if_no_sut` parameter.

        Examples:
        | Screenshot | (67, 33), imagelocation("OtherCorner") |
        | Screenshot | RxLocation, RxLocation + (140,100) | my_screenshot.png | 100, 150, 200, 300 |
        See [http://docs.testplant.com/ePF/SenseTalk/stk-results-reporting.htm#capturescreen-command|eggPlant docs]
        for details.            
        """

        screenshot_path = self.take_screenshot(rectangle, file_path, highlight_rectangle, error_if_no_sut_connection)
        self.log_embedded_image(screenshot_path)

    @keyword
    def run_command(self, command):
        """
        Sends the requested command to eggPlant server via XML RPC.
        Allows you to call any eggPlant function or script beyond available keywords.

        Returns the `Result` value of the XML RPC response, although it might be 
        a result of a previous script.

        The `command` is a string in the eggDrive format. Quotes have to be escaped.
        
        Examples:
        | Run Command | myScript arg1, arg2 |
        | Run Command | click \\"someImage\\" |
        """

        result = self.execute(command)
        return result

    @keyword
    def open_session(self, suite='', close_previously_open_session=True):
        """
        Opens a session with the specified eggPlant Suite.
        Has to be called before test execution.
        The keyword also checks current eggpPant version and logs a warning in case of incompatibility.

        The `suite` parameter (optional) is a path to the eggPlant `.suite` file which session is to open.
        If not specified, the default suite is taken, which was set during library init/import.
        
        By default if the is a previously open session, it is closed automatically.
        This can be disabled using the `close_previously_open_session` parameter.
        """
        s = suite
        if not suite:
            s = self.eggplant_suite
        log.debug("Open the eggPlant session with the test suite: {}".format(s))
        try:
            out = self.eggplant_server.startsession(s)
            log.debug(out)
            
        except xmlrpc.client.Fault as e:
            if close_previously_open_session and "BUSY: Session in progress" in e.faultString:
                    log.info("Old session busy - close it automatically")
                    self.close_session()                    
                    out = self.eggplant_server.startsession(s)
                    log.debug(out)            
            else:
                raise e
        
        except ConnectionRefusedError as e:
            log.info(f"ConnectionRefusedError - {e}")
            raise Exception("Failed connecting to eggPlant - check it's running in eggDrive mode")

        # check eggplant version compatibility first - but only once
        if not self.eggplant_version_checked:
            self.execute(f'if EggplantVersion().eggplant < "{EGGPLANT_VERSION_MIN}" then LogWarning '
                         '!"Incompatible eggplant version detected - [[EggplantVersion().eggplant]]. '
                         f'Min. version required - {EGGPLANT_VERSION_MIN}. '
                         'See README for more information."')
            self.eggplant_version_checked = True

    @keyword
    def close_session(self, suite=''):
        """
        Closes the session with the specified eggPlant Suite.
        Has to be called after test execution before opening a new session with the same eggPlant Suite.
        If the requested session is not open, a warning is logged.

        The `suite` parameter (optional) is a path to the eggPlant `.suite` file which session is to close.
        If not specified, the last open suite is taken.
        """
        s = suite
        if not suite:
            s = self.eggplant_suite
        log.debug("Close the eggPlant session with the test suite: {}".format(s))
        try:
            out = self.eggplant_server.endsession(s)
            log.debug(out)
        except xmlrpc.client.Fault as e:
            log.info("Fault code:{}. Fault string: {}".format(e.faultCode, e.faultString))
            if "Can't End Session -- No Session is Active" in e.faultString:
                log.warn("No open eggPlant session to close!")
            else:
                raise e
        except ConnectionRefusedError as e:
            log.info(f"ConnectionRefusedError - {e}")
            raise Exception("Failed connecting to eggPlant - check it's running in eggDrive mode")

    @keyword
    def start_movie(self, file_path='', fps=15, compression_rate=1, highlighting=True, extra_time=5):
        """
        Starts video recording into the specified file and returns the absolute path to it.
        
        The `file_path` (optional) is relative to the current Robot Framework output dir.
        If not specified, the default name is used.

        The `fps` parameter defines frames per second.
        
        The `compression_rate` adjusts the compression amount of the movie. The value range is (0, 1].
        Set the rate lower to decrease the file size and video quality.

        The `highlighting` determines whether the search rectangles are highlighted in the movie.

        The recording continues for the `extra_time` seconds after the StopMovie command was executed.

        See more in [http://docs.eggplantsoftware.com/ePF/SenseTalk/stk-results-reporting.htm#startmovie-command|eggplant docs].        
        """
        path = file_path

        if not file_path:
            path = "Movies\\Movie__{0}.mp4".format(datetime.now().strftime('%Y-%m-%d__%H_%M_%S'))

        if path and os.path.isabs(path):
            raise RuntimeError("Given file_path='%s' must be relative to Robot output dir" % path)

        # image output file path is relative to robot framework output
        full_path = os.path.join(BuiltIn().get_variable_value("${OUTPUT DIR}"), path)
        if not os.path.exists(os.path.split(full_path)[0]):
            os.makedirs(os.path.split(full_path)[0])

        self.execute(f'StartMovie "{full_path}", framesPerSecond:{fps}, compressionRate:{compression_rate}, '
                     f'imageHighlighting:{highlighting}, extraTime:{extra_time}')

        # and embed it into the RF log
        log.info('Start video recording')
        self.log_embedded_video(path)
        self.current_movie_path = path  # save it to embed video in the log in case of errors
        return path

    @keyword
    def stop_movie(self, error_if_no_movie_started=False):
        """
        Stops current video recording.

        Normally there is no error thrown in case of no active recording,
        but it can be enabled setting the `error_if_no_movie_started` parameter.
        """
        log.info("Stop video recording.")
        try:
            self.execute('StopMovie')
            if self.current_movie_path:
                self.log_embedded_video(self.current_movie_path)
            else:
                log.info("Saving video into log failed - current recording file path empty!")
        except xmlrpc.client.Fault as e:
            no_movie_error = 'StopMovie is not allowed -- there is no movie being recorded'
            if no_movie_error in e.faultString:
                log.debug("XMLRPC execution failure! Fault code:{}. Fault string: {}".
                          format(e.faultCode, e.faultString))
                if error_if_no_movie_started:
                    raise Exception(e.faultString)
                else:
                    log.info(e.faultString)
            else:
                raise e
        finally:
            self.current_movie_path = None  # reset it in any case
