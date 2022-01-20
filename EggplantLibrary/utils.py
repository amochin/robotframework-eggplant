import logging as log
import ast
import warnings


def remove_unreadable_characters_at_start(string):
    """
    Removes non ASCII characters from the string start as eggPlant files often begin with some strange symbols.
    The string gets also stripped (blank characters at start and end will be removed)
    :param string:
    :return: the processed string
    """
    stripped_string = string.strip()

    chars_to_remove = ''
    for c in stripped_string:
        if not 0 < ord(c) < 127:
            chars_to_remove += c
    stripped_string = stripped_string.lstrip(chars_to_remove)
    return stripped_string

    # ---------- eggPlant result type conversion ------------


def remove_at_symbol_before_quotes(input_string):
    """
    Change in eggPlant 21.2.0 - string values inside a list which contain special characters
    like \n get a @ in front --> @"my special \n string"
    """
    s = str(input_string)
    s = s.replace('@"', '"')
    log.debug(f"Removed possible @ symbol in front of string values in the list. Result: {s}")
    return s


def to_bool(input_value):
    s = str(input_value).lower()
    if s == "true":
        return True
    if s == "false":
        return False
    raise ValueError("{} can't be converted to bool".format(input_value))


def quote_string_if_not_num_or_bool(input_string):
    s = convert_to_num_bool_or_string(input_string)
    if isinstance(s, str):
        s = repr(s)  # for possible \n characters inside
    return str(s)


def convert_to_num_bool_or_string(input_string):
    s = input_string
    for fn in (int, float, to_bool):
        try:
            s = fn(input_string)
            break
        except ValueError:
            continue
    return s


def unquote_bool_values(input_string):
    """
    Change in eggPlant 21.2.0 - bool values inside a list get quoted [false, true] --> ["False", "True"]
    """
    s = input_string.replace('"True"', 'True')
    s = s.replace('"False"', 'False')
    log.debug(f"Removed double quotes around possible bool values in the list. Result: {s}")
    return s


def count_free_closing_brackets(input_string, start_index=0):
    """
    DEPRECATED - No more needed since eggPlant 20.1.0 as it uses new list format
    and quotes string value in returned lists.
    The function has been used to handle lists returned by eggplant which contain unpaired closing brackets.
    Examples of returned lists:
    - eggPlant before 20.1.0 - (xyz, (1234,he(llo), abc)))
    - eggPlant after 20.1.0 - ["xyz", [1234,"he(llo)", "abc)"]]
    Returns count of free list closing brackets in the string starting from specified index.

    """
    warnings.warn("The 'count_free_closing_brackets' function should not be needed since eggPlant 20.1.0"
                  " as it uses new list format and quotes string value in returned lists", DeprecationWarning, 2)

    count_closing = 0
    count_starting = 0
    length = len(input_string)
    count_closing_all = 0
    count_starting_all = 0
    i_remember_closing = 0
    i_remember_starting = 0

    for i in range(start_index, length):
        if input_string[i] == ')':
            # is this bracket a list closure?

            if i < length - 1:  # don't count next brackets on the string end - they're definitely list end
                # we need only brackets which might close a list - and they must be followed by these characters
                if not input_string[i + 1] in [')', ',']:
                    i_remember_closing = i
                    continue
            # alright, this seems to be a list closure
            count_closing += 1
        # calculate list open brackets as well - we deduct them from all found closure brackets
        if input_string[i] == '(':
            if i > 0:  # but don't check next brackets on the string beginning - they're definitely list start
                # we need only brackets which might start a list - and they must be followed by these characters
                if not input_string[i - 1] in ['(', ',']:
                    i_remember_starting = i
                    continue
            # alright, this seems to be a list start
            count_starting += 1
    if i_remember_closing + i_remember_starting == 0:
        return count_closing - count_starting

    # Error handling for lists in lists and strings with brackets
    # e.g. "(3163,(302,336),(300,270,1828,990),(280,318,488,990),S Spandau DB-Berlin Westkreuz (Stadtbahn))"
    for i in range(0, length):
        if input_string[i] == ')':
            # check if this bracket is a list closure
            if i < length - 1:  # but don't check next brackets on the string end - they're definitely list end
                # we need only brackets which might close a list - and they must be followed by these characters
                if not input_string[i + 1] in [')', ',']:
                    continue
            # alright, this seems to be a list closure
            count_closing_all += 1
        # calculate list open brackets as well - we deduct them from all found closure brackets
        if input_string[i] == '(':
            if i > 0:  # but don't check next brackets on the string beginning - they're definitely list start
                # we need only brackets which might start a list - and they must be followed by these characters
                if not input_string[i - 1] in ['(', ',']:
                    continue
            # alright, this seems to be a list start
            count_starting_all += 1
    # alright, this seems to be a list start
    if count_starting_all != count_closing_all and input_string.count('(') == input_string.count(')'):
        if count_starting_all < count_closing_all and i_remember_starting > 0:
            count_starting += 1
        elif i_remember_closing > 0:
            count_closing += 1
    return count_closing - count_starting


def quote_inner_strings(parent_str):
    cur_val_start = 0
    result_str = ""
    list_start_brackets = 0
    length = len(parent_str)

    # not a list in eggplant format? Just give the entire string back
    if not parent_str.startswith("["):
        log.debug("Wrong list format - use the entire value as a string")
        return quote_string_if_not_num_or_bool(parent_str)

    # it's a list in eggplant format? then go through the string and separate values
    for i in range(0, length):
        # new value starts?
        if parent_str[i] in ["[", " "]:
            # new value begins if we increased the counter before, otherwise it's just an inner string character
            if i == cur_val_start:
                result_str += parent_str[i]
                cur_val_start += 1

                # count list beginnings - we need them later to calculate expected list endings
                if parent_str[i] == "[":
                    list_start_brackets += 1

        # current value ends?
        if parent_str[i] in ["]", ","]:
            # check if this closing bracket just part of an inner string?
            if parent_str[i] == "]":
                if i < length - 1:  # no string end yet? otherwise it's definitely a real list end
                    if not parent_str[i + 1] in ["]", ","]:  # only one of the symbols can follow after real list end
                        continue  # otherwise it's just an inner string character - carry on
                    # decrease counter of list start brackets
                    list_start_brackets -= 1

            # current value ends - save it
            item = parent_str[cur_val_start:i]

            if len(item) > 0 or parent_str[i - 1] in (",", "["):
                # to avoid empty items in cases like ']]' and '],'
                # but do add empties in cases like ',]' and '[,' - eggPlant returns it like this
                result_str += quote_string_if_not_num_or_bool(item)

            result_str += parent_str[i]
            cur_val_start = i + 1

    if cur_val_start < length:
        item = parent_str[cur_val_start:length]
        result_str += quote_string_if_not_num_or_bool(item)
    return result_str


def tuple2list(tuple_to_convert):
    """
    Converts a tuple of tuples of tuples ... into a list of lists of lists
            (1, 2, ('A', 'B', ('alpha', 'beta', 'gamma'), 'C'), 3) -->
        --> [1, 2, ['A', 'B', ['alpha', 'beta', 'gamma'], 'C'], 3]
    https://stackoverflow.com/questions/1014352/how-do-i-convert-a-nested-tuple-of-tuples-and-lists-to-lists-of-lists-in-python
    """
    if not isinstance(tuple_to_convert, (list, tuple)):
        return tuple_to_convert
    return list(map(tuple2list, tuple_to_convert))


def list2tuple(list_to_convert):
    """
    Converts a list of lists of lists ... into a tuple of tuples of tuples
            [1, 2, ['A', 'B', ['alpha', 'beta', 'gamma'], 'C'], 3] -->
        --> (1, 2, ('A', 'B', ('alpha', 'beta', 'gamma'), 'C'), 3)

    https://stackoverflow.com/questions/1014352/how-do-i-convert-a-nested-tuple-of-tuples-and-lists-to-lists-of-lists-in-python
    """
    if not isinstance(list_to_convert, (list, tuple)):
        return list_to_convert
    return tuple(map(list2tuple, list_to_convert))


def auto_convert(s):
    """
    Tries to convert the input value into one of Python data types.
    This function is designed specially for converting eggPlant result strings in the 'RunWithNewResults' mode.
    Values of a list get special processing:
     - String values "True" and "False" are converted into booleans
     - At ('@') symbol in front of string values is removed: @"special \n string" --> "special \n string"
    """
    if s == '':
        return ''
    try:
        log.debug("Trying to evaluate the string as Python literal: {}".format(s))
        is_list = s.startswith("[") and s.endswith("]")
        if is_list:
            log.debug("String recognized as a list")
            s = unquote_bool_values(s)
            s = remove_at_symbol_before_quotes(s)
        val = ast.literal_eval(s)  # Magic!!! https://docs.python.org/3/library/ast.html#ast.literal_eval
    except (ValueError, SyntaxError) as e:
        try:
            log.debug("Error occurred - {}".format(e))
            log.debug("Trying to quote all non digital values.")
            quoted = quote_inner_strings(s)
            log.debug("Result after quoting: {}".format(quoted))
            val = ast.literal_eval(quoted)
        except Exception as e:
            log.debug("Error again - {}".format(e))
            log.debug("Give up and return the original value just as a string")
            val = str(s)

    return val


def single_quote_to_double(input_value):
    """
    Special for eggplant lists - replaces single quotes around all values with double quotes
    """
    s = str(input_value)
    s = s.replace("['", "[\"")  # ['A'] --> ["A']
    s = s.replace("']", "\"]")  # ['A'] --> ['A"]
    s = s.replace("',", "\",")  # ['A', 'B'] --> ['A", 'B']
    s = s.replace(",'", ",\"")  # ['A','B'] --> ['A',"B']
    s = s.replace(", '", ", \"")  # ['A', 'B'] --> ['A', "B']
    return s
