#!/usr/bin/env python
import os
import sys

from xml.dom.minidom import parse

# copied from gn_helpers.py
if sys.version_info[0] < 3:
    string_types = basestring
else:
    string_types = str


class GNException(Exception):
    pass


def ToGNString(value, allow_dicts=True):
    """Returns a stringified GN equivalent of the Python value.

    allow_dicts indicates if this function will allow converting dictionaries
    to GN scopes. This is only possible at the top level, you can't nest a
    GN scope in a list, so this should be set to False for recursive calls."""
    if isinstance(value, string_types):
        if value.find('\n') >= 0:
            raise GNException("Trying to print a string with a newline in it.")
        return '"' + \
               value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$') + \
               '"'

    if isinstance(value, bool):
        if value:
            return "true"
        return "false"

    if isinstance(value, list):
        return '[ %s ]' % ', '.join(ToGNString(v) for v in value)

    if isinstance(value, dict):
        if not allow_dicts:
            raise GNException("Attempting to recursively print a dictionary.")
        result = ""
        for key in sorted(value):
            if not isinstance(key, string_types):
                raise GNException("Dictionary key is not a string.")
            result += "%s = %s\n" % (key, ToGNString(value[key], False))
        return result

    if isinstance(value, int):
        return str(value)

    raise GNException("Unsupported type when printing to GN.")


def get_set_files(sets, var):
    files = []
    for file in sets[var]:
        if file.startswith('${'):
            setname = file[2:-1]
            files.extend(get_set_files(sets, setname))
        else:
            files.append(file)
    return files


def main(filename, *variable_names):
    with open(filename) as f:
        tree = parse(f)
    sets = {}
    for set in tree.getElementsByTagName('set'):
        filenames = []
        for f in set.firstChild.nodeValue.split('\n'):
            path = f.strip()
            if not path or path.startswith('${'):
                continue
            filenames.append(path)
        sets[set.getAttribute('var')] = filenames

    ret = {}
    for var in variable_names:
        ret[var] = sets[var]

    print(ToGNString(ret))


if __name__ == '__main__':
    main(*sys.argv[1:])
