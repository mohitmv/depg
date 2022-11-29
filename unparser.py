#! /usr/bin/env python3

# Author: Mohit Saini (mohitsaini1196@gmail.com)

import json

BUILD_FILE_TOP_COMMENT = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

"""

KEY_PREFERENCES_MAP = {"name": 100, "hdrs": 101, "src": 102, "srcs": 103,
                       "package": 104, "public_deps": 105, "private_deps": 106,
                       "deps": 1000}

UNKNOWN_KEY_PREFERENCE = 500


def isComplexList(l):
    if len(l) == 0:
        return False
    if isinstance(l[0], dict):
        return True
    if isinstance(l[0], (list, tuple)):
        return True
    return False


class TargetUnparser:
    def unparse(self, target, indent=4):
        output = dict(s="")
        def sortKeys(keys):
            if len(KEY_PREFERENCES_MAP) > 0:
                keys = sorted(keys, key=lambda x: \
                    (KEY_PREFERENCES_MAP.get(x, UNKNOWN_KEY_PREFERENCE), x))
            return keys

        def printFuncArgs(args, kwargs, depth):
            output['s'] += "(\n"
            for index, arg in enumerate(args):
                printD(None, arg, depth)
                if index < len(args) - 1 or len(kwargs) > 0:
                    output["s"] += ",\n"
            if len(kwargs) > 0:
                keys = sortKeys(kwargs.keys())
                for index, k in enumerate(keys):
                    printD(k, kwargs[k], depth)
                    if index < len(keys) - 1:
                        output['s'] += ',\n'
            output["s"] += ")"

        def printD(key, value, depth, kv_sep=' = '):
            output['s'] += ' '*depth
            if key is not None:
                output['s'] += key + kv_sep
            if isinstance(value, dict):
                if len(value) == 0:
                    output["s"] += "{}"
                else:
                    output["s"] += "{\n"
                    keys = sortKeys(value.keys())
                    for index, k in enumerate(keys):
                        printD(json.dumps(k),
                               value[k],
                               depth + indent,
                               kv_sep=": ")
                        if index < len(keys) - 1:
                            output['s'] += ',\n'
                    output["s"] += "}"
            elif isinstance(value, list):
                is_complex_list = isComplexList(value)
                if is_complex_list:
                    output['s'] += "[\n"
                else:
                    output['s'] += "[ "
                for index, v in enumerate(value):
                    required_indent = 0 if index == 0 else \
                        (depth + 2 +
                         (0 if key is None else len(key) + len(kv_sep)))
                    if is_complex_list:
                        required_indent = depth + indent
                    printD(None, v, required_indent)
                    if index < len(value) - 1:
                        output['s'] += ',\n'
                output['s'] += ' ]'
            else:
                if isinstance(value, bool):
                    output['s'] += str(value)
                else:
                    output['s'] += json.dumps(value)
        output['s'] += target['type'].funcName()
        target.pop("type")
        printFuncArgs([], target, indent)
        return output['s']


class BuildFileUnparser:
    def __init__(self):
        self.target_unparser = TargetUnparser()

    def unparse(self, targets):
        output = BUILD_FILE_TOP_COMMENT
        for tname, target in targets.items():
            output += self.target_unparser.unparse(target) + "\n\n"
        return output

def unparse(build_file_struct):
    return BuildFileUnparser().unparse(build_file_struct)
