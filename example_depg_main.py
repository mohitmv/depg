#! /usr/bin/env python3

# Author: Mohit Saini (mohitsaini1196@gmail.com)

"""
Usage:
./tools/depg/main.py a/b/c.cpp z/g.hpp
This will update the targets in a/b/BUILD and z/BUILD as per changed files.

Read `tools/depg/README.md` and
     `tools/depg/implementation_details_README.md` to know more about depg.
"""

# pylint: disable=missing-function-docstring,invalid-name,no-else-return
# pylint: disable=unused-import

import argparse
import os

import depg.depg as depg

def getConfigs():
    configs = depg.getDefaultConfigs()
    configs.THIRD_PARTY_TARGET_BUILD_FILES = ["third_party/targets/BUILD"]
    configs.TOP_DIRECTORY_LIST = ["sage", "common", "testing", "third_party"]
    return configs


def getArgs():
    """Return the object with parsed command line arguments."""
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        'paths', nargs='*',
        help="List of changed files/directories in this repo. If a directory "
             "is specified then all files will be considered recursively.")
    parser.add_argument(
        "--output_directory",
        default=".",
        help="Directory where generated BUILD files will be written. "
             "Default: Current directory. A custom directory like '/tmp/abc' "
             "can be used here to only dump the generated BUILD files without "
             "overwriting the existing BUILD files.")
    parser.add_argument("--dont_gen_build", action='store_true', default=False)
    parser.add_argument("--gen_cmake", action='store_true', default=False)
    parser.add_argument("--force_override_build_files", action='store_true', default=False)
    parser.add_argument("--cmake_build_dir", default="build")
    return parser.parse_args()

def main():
    source_directory = os.path.abspath("ms/ctwik_experimental")
    os.chdir(source_directory)
    args = getArgs()
    configs = getConfigs()
    configs.force_override_build_files = args.force_override_build_files
    depg_main = depg.Depg(source_directory, configs)
    if not args.dont_gen_build:
        depg_main.regenerateBuildFiles(args.paths, args.output_directory)
    if args.gen_cmake:
        depg_main.genCmake(args.paths, args.cmake_build_dir)

if __name__ == "__main__":
    main()
