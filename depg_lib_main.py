#! /usr/bin/env python3

# Author: Mohit Saini (mohitsaini1196@gmail.com)

"""
The entry point of DepG library. Read the `README.md` for more details.
"""

# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring

import os

from . import target_graph_builder
from .default_configs import getDefaultConfigs
from . import merge_build_file
from . import parser
from . import common


def getHeaderPrefixesMap(third_p_build_files):
    """
    A map from header prefix to target.
    It's used for detecting the dependency target. eg: if a program includes the
    header "glog/logging.h", it means we can can say this program depends on the
    glog target. In this case the prefix "glog/" is present in header prefix
    map with glog-target as corrosponding value.
    Currently we populate the header prefix map for third-party libraries.
    Note: All the third-party targets are manually declared.
    """
    output = {}
    for build_file in third_p_build_files:
        directory = os.path.dirname(build_file) or "."
        targets_map = parser.readBuildFile(build_file, directory)
        for tname, target in targets_map.items():
            for i in target.get("header_prefix", []):
                output[i] = f"{directory}/{tname}"
    return output


def validateWorkingDirectory(source_directory):
    assert source_directory == os.getcwd(), \
            "Current directory should be source_directory."


def preprocessConfig(configs):
    configs.CPP_EXTENSIONS = configs.CPP_HEADER_EXTENSIONS + configs.CPP_SOURCE_EXTENSIONS
    if configs.HEADER_PREFIXES_MAP is None:
        configs.HEADER_PREFIXES_MAP = getHeaderPrefixesMap(configs.THIRD_PARTY_TARGET_BUILD_FILES)
        configs.DEPG_DEPS_CACHE_CHECKSUM = ":".join(common.getFileCheckSum(x)
                                            for x in configs.THIRD_PARTY_TARGET_BUILD_FILES)
    top_dirs = set(common.toRelativePaths(configs.TOP_DIRECTORY_LIST))
    configs.IGNORED_PATHS |= set(i for i in os.listdir(".") if i not in top_dirs)
    return configs


class Depg:
    def __init__(self, source_directory, configs):
        validateWorkingDirectory(source_directory)
        self.configs = preprocessConfig(configs)
        self.deps_parser = target_graph_builder.TargetGraphBuilder(self.configs)

    def autoGenBuildFileMap(self, paths):
        target_names = target_graph_builder.changedPathsToTargetNames(
            paths, self.configs)
        targets_map = self.deps_parser.getDeps(target_names)
        build_files_map = merge_build_file.depgTargetsToLocalTargets(targets_map)
        return build_files_map

    def regenerateBuildFiles(self, paths, output_directory="."):
        build_files_map = self.autoGenBuildFileMap(paths)
        merge_build_file.regenerateBuildFiles(build_files_map,
                output_directory=output_directory,
                force_override_build_files=self.configs.force_override_build_files)
