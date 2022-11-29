#! /usr/bin/env python3

import os
import common
from collections import OrderedDict
import targets

# import merge_build_file

def readBuildFile(filename, file_content):
    output = OrderedDict()
    def typeFunc(target_type):
        def func(**args):
            args['type'] = target_type
            output[args['name']] = args
        return func
    func_map = {}
    for target_type in targets.TargetType:
        func_map[target_type.funcName()] = typeFunc(target_type)
    locals().update(func_map)
    exec(file_content)
    directory = os.path.dirname(filename)
    def expandDep(dep):
        if dep.startswith(":"):
            return directory + "/" + dep[1:]
        else:
            return dep.replace(":", "/")
    for tname, target in output.items():
        for field in ['public_deps', 'private_deps']:
            if field not in target:
                continue
            target[field] = [expandDep(dep) for dep in target[field]]
    return output


filename = "configs/third_party.py"

# os.chdir("../ms/ctwik_experimental")

print(readBuildFile(filename, common.readFile(filename)))
