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
