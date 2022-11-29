#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=invalid-name,too-many-branches

import json

import configs.configs as configs

def isComplexList(l):
    if len(l) == 0:
        return False
    if isinstance(l[0], dict):
        return True
    if isinstance(l[0], (list, tuple)):
        return True
    return False

def getTargetString(target, indent=4):
    target_type = target.type
    target = dict(target)
    target.pop("type")
    if target_type in configs.CPP_TARGETS:
        target.pop("deps")
    output = dict(s="")
    def printD(key, value, depth):
        output['s'] += ' '*depth
        if key is not None:
            output['s'] += key + '='
        if isinstance(value, dict):
            output['s'] += "dict(\n"
            for index, (k, v) in enumerate(value.items()):
                printD(k, v, depth + indent)
                if index < len(value) - 1:
                    output['s'] += ',\n'
            output['s'] += ')'
        elif isinstance(value, list):
            is_complex_list = isComplexList(value)
            if is_complex_list:
                output['s'] += "[\n"
            else:
                output['s'] += "[ "
            for index, v in enumerate(value):
                required_indent = 0 if index == 0 else (depth + len(key) + 3)
                if is_complex_list:
                    required_indent = depth + indent
                printD(None, v, required_indent)
                if index < len(value) - 1:
                    output['s'] += ',\n'
            output['s'] += ' ]'
        else:
            if isinstance(value, bool):
                output['s'] += str(value)
            elif key == 'host_type':
                output['s'] += value
            else:
                output['s'] += json.dumps(value)
    output['s'] = "br." + target_type.funcName() + "(\n"
    for index, (k, v) in enumerate(target.items()):
        printD(k, v, indent)
        if index < len(target) - 1:
            output['s'] += ',\n'
    output['s'] += ")"
    return output['s']


def getTargetsString(targets):
    output = "\n\n"
    for _, target in targets.items():
        output += getTargetString(target) + "\n\n"
    return output
