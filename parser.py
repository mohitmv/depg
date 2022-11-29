#! /usr/bin/env python3

# Author: Mohit Saini (mohitsaini1196@gmail.com)

import os
from collections import OrderedDict

from . import targets
from . import common
from . import utils

def readBuildFile(filepath, directory=None, file_content=None):
    directory = directory or os.path.dirname(filepath) or "."
    file_content  = file_content or common.readFile(filepath)
    output = OrderedDict()
    def typeFunc(target_type):
        def func(**args):
            args['type'] = target_type
            output[args['name']] = utils.Object(args)
        return func
    func_map = {}
    for target_type in targets.TargetType:
        func_map[target_type.funcName()] = typeFunc(target_type)
    locals().update(func_map)
    exec(file_content)
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

def readBuildFilesAndConvertToFullTargetNames(build_files):
    output = {}
    for build_file in build_files:
        output.update(readBuildFileAndConvertToFullTargetNames(build_file))
    return output


def readBuildFileAndConvertToFullTargetNames(build_file):
    output = collections.OrderedDict()
    directory = os.path.dirname(build_file)
    targets = merge_build_file.readBuildFile(build_file)
    for tname, target in targets.items():
        for field in ["name", "src"]:
            if field not in target:
                continue
            target[field] = f"{directory}/{target[field]}"
        for field in ["srcs", "hdrs"]:
            if field not in target:
                continue
            target[field] = [f"{directory}/{x}" for x in target[field]]
        for field in ["public_deps", "private_deps"]:
            if field not in target:
                continue
            new_list = []
            for x in target[field]:
                if x.startswith(":"):
                    x = f"{directory}{x}"
                x = x.replace(":", "/")
                new_list.append(x)
            target[field] = new_list
        output[target["name"]] = target
    return output


