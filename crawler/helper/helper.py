import json


def read_json(filename):
    """
    Reads a json from filename
    :param filename:
    :type filename: str
    :return:
    :rtype: dict
    """
    f = open(filename, 'r')
    json_dict = json.loads(f.read())
    f.close()
    return json_dict


def convert_int(string):
    """
    Tries to convert a string to an int and returns None if not possible
    :param string: to be converted string
    :type string: str
    :return: the returned int or none
    :rtype: int
    """
    try:
        x = int(string)
    except ValueError:
        x = None
    return x


def isclose(a, b, rel_tol=0.2, abs_tol=0.5):
    """
    Check if two floats are close to each other based on a rel and absolute tolerance
    https://stackoverflow.com/questions/5595425/what-is-the-best-way-to-compare-floats-for-almost-equality-in-python
    :param a:
    :type a: float
    :param b:
    :type b: float
    :param rel_tol:
    :type rel_tol: float
    :param abs_tol:
    :type abs_tol: float
    :return: if they are close
    :rtype: bool
    """
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def remove_text_inside_brackets(text, brackets="()[]"):
    """
    Found at: https://stackoverflow.com/questions/14596884/remove-text-between-and
    :param text:
    :type text:
    :param brackets:
    :type brackets:
    :return:
    :rtype:
    """
    count = [0] * (len(brackets) // 2)  # count open/close brackets
    saved_chars = []
    for character in text:
        for i, b in enumerate(brackets):
            if character == b:  # found bracket
                kind, is_close = divmod(i, 2)
                count[kind] += (-1) ** is_close  # `+1`: open, `-1`: close
                if count[kind] < 0:  # unbalanced bracket
                    count[kind] = 0  # keep it
                else:  # found bracket to remove
                    break
        else:  # character is not a [balanced] bracket
            if not any(count):  # outside brackets
                saved_chars.append(character)
    return ''.join(saved_chars)


def get_unit_from_item_name(name):
    """
    Converts a meal name from myfittnesspal of the form Brand - Name, unit into its part
    :param name:
    :type name:
    :return:
    :rtype:
    """
    def unit_detector(string):
        string = string.split(' ', 1)
        number = convert_int(string[0])
        # if this doesn't work try with eval e.g for 5/3
        if number is None:
            try:
                number = eval(string[0])
            except:
                return None, None
            if type(number) not in (int, float):
                return None, None
        unit = None
        if len(string) == 2:
            unit = string[1]
        return number, unit

    name_split = name.split(', ')
    curr = ""
    amt, units = None, None
    for split in reversed(name_split):

        curr = split if curr == "" else split + ', ' + curr
        result = unit_detector(curr)
        if result is not None:
            amt, units = result
            name = name.rstrip(curr).rstrip(',')
            break
    name_split = name.split(' - ', 1)
    if len(name_split) == 2:
        return name_split[1], name_split[0], amt, units
    return name, None, amt, units
