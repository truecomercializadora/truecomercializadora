"""
A module designed, to work with math problems, from a general perspective.
Therefore, no business knowledge should be required in order to understand
any of the functions defined here.
"""

import math

def convert_size(size_bytes: int) -> str:
    '''
    Return a string with the size converted to bytes units from an int value
    '''
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])