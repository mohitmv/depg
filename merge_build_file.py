#! /usr/bin/env python3

# Author: Mohit Saini (mohitsaini1196@gmail.com)

# pylint: disable=missing-function-docstring,invalid-name
# pylint: disable=missing-class-docstring,unused-import
# pylint: disable=missing-module-docstring

from collections import OrderedDict
import json
import os

from . import targets
from . import common
from . import parser
from . import unparser

# Soft-merge the existing params of a target on these field.
# Rest of the params will be force merged by the auto-generated params.
SOFT_MERGE_PARAMS = set(["name", "type"])

VERY_FORCE_MERGE_PARAMS = set(["srcs", "src", "hdrs"])

# If this word is present in a BUILD file, it won't be auto-updated.
DONT_AUTO_GENERATE_MARKER = "DO_NOT_AUTO_GENERATE_THIS_BUILD_FILE"

def mergeDict(d1, d2):
    for k in VERY_FORCE_MERGE_PARAMS:
        if k in d1:
            d1.pop(k)
    for k, v in d2.items():
        soft_merge = k in SOFT_MERGE_PARAMS
        if not soft_merge or (k not in d1):
            d1[k] = v
    return d1

def trimPrefix(a, b):
    assert a.startswith(b)
    return a[len(b):]

def depgTargetToLocalTarget(target):
    directory = target['name'].rsplit("/", 1)[0]
    prefix = directory + "/"
    for field in ['name', 'src']:
        if field not in target:
            continue
        target[field] = trimPrefix(target[field], prefix)
    for field in ['srcs', 'hdrs']:
        if field not in target:
            continue
        target[field] = [trimPrefix(x, prefix) for x in target[field]]
    for field in ['private_deps', 'public_deps']:
        if field not in target:
            continue
        other_deps = []
        local_deps = []
        for dep in target[field]:
            if os.path.dirname(dep) == directory:
                local_deps.append(":" + os.path.basename(dep))
            else:

                other_deps.append(f"{os.path.dirname(dep)}:{os.path.basename(dep)}")
        target[field] = local_deps + other_deps
    return (directory, target)


def depgTargetsToLocalTargets(targets_map):
    """
    Here @output is a map(BUILD file path -> OrderedDict(target name -> target))
    """
    output = {}
    for tname, target in targets_map.items():
        directory, target = depgTargetToLocalTarget(target)
        filename = directory + "/BUILD"
        if filename not in output:
            output[filename] = OrderedDict()
        output[filename][target['name']] = target
    return output


def canAutoUpdateTarget(target):
    """
    Given a target, check if we are allowed to auto-update it, based
    on this special tag.
    """
    return "DO_NOT_AUTO_GENERATE_THIS_RULE" not in target.get('tags', [])

def merge(a1: OrderedDict, a2: OrderedDict):
    """Merge @a2 in @a1."""
    for tname, target in a2.items():
        if tname in a1 and canAutoUpdateTarget(a1[tname]):
            mergeDict(a1[tname], target)
        if tname not in a1:
            a1[tname] = target
    return a1


def regenerateBuildFiles(auto_gen_build_files_map, output_directory=".", force_override_build_files=False):
    for build_file, build_file_struct in auto_gen_build_files_map.items():
        old_build_file_struct = None
        build_file_path = f"{output_directory}/{build_file}"
        if os.path.isfile(build_file_path):
            file_content = common.readFile(build_file_path)
            if DONT_AUTO_GENERATE_MARKER in file_content:
                continue
            if not force_override_build_files:
                old_build_file_struct = parser.readBuildFile(
                    build_file_path,
                    directory=os.path.dirname(build_file),
                    file_content=file_content)
        if old_build_file_struct is not None:
            build_file_struct = merge(
                old_build_file_struct, build_file_struct)
        filename = os.path.join(output_directory, build_file)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        content = unparser.unparse(build_file_struct)
        common.writeFile(filename, content)
