#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring

from . import std_headers
from .utils import Object

def customHeaderIdentificationHandler(header):
    """
    A couple of headers don't fit into the target identification heuristics
    we have implemented in CppSourceDepsParser. We need custom handler to
    identify the corresponding targets for those headers.
    """
    return None

def getDefaultConfigs():
    configs = Object()
    # Top level directories starting with any of these strings are not
    # source code directory. Build system should ignore them. DepG should not
    # visit these directories to generate targets.
    #
    # Note: The enteries listed here are checked as string-prefix
    #       not the path prefix.
    # Eg : ("ab/cd" is a path-prefix of path "ab/cd/xyz.txt")
    # Eg : ("ab/c" is NOT a path-prefix of path "ab/cd/xyz.txt")
    # Eg : ("ab/c" is a string-prefix of path "ab/cd/xyz.txt")
    # Eg : ("ab/cd/" is a path-prefix of path "ab/cd/xyz.txt")
    # Eg : ("ab/cd/xyz.txt" is a path-prefix of path "ab/cd/xyz.txt")
    #
    # Hence top level directories like `build-out`, `build-dbg`,
    # `build-x` etc. will be forbidden.
    configs.FORBIDDEN_TOP_LEVEL_DIRS_STARTS_WITH = ("build", "third-party", "tools")

    configs.FORBIDDEN_PATHS = set([])

    # Ignored paths are different from forbidden paths. These paths will be ignored
    # by default. However if these paths are explicitly chosen, they will work as
    # usual. For example, we don't want to build the code in experimental
    # directories if someone choose to build root directory. However the
    # code in experimental should be compliable if the 'experimental' directory is
    # explicitly chosen.
    configs.IGNORED_PATHS = set(["experimental"])


    configs.CPP_HEADER_EXTENSIONS = ("-inl.hpp", ".hpp", ".h")
    configs.CPP_SOURCE_EXTENSIONS = (".cpp", ".cc", ".c")
    configs.PROTO_HEADER_EXTENSION = ".pb.h"
    configs.GRPC_HEADER_EXTENSION = ".grpc.pb.h"
    configs.PROTO_EXTENSION = ".proto"
    configs.TEST_FILE_EXTENSION = "_test.cpp"

    configs.IGNORED_HEADERS = set(["options.pb.h"])


    configs.IGNORE_EXISTANCE = set([])

    configs.CACHE_DIRECTORY = "build/.depg/cache"

    configs.BUILD_FILE_NAME = "BUILD"

    configs.THIRD_PARTY_TARGET_BUILD_FILES = []
    configs.HEADER_PREFIXES_MAP = None

    configs.INCLUDE_PATHS = []

    configs.CXX_FLAGS = []

    configs.LINK_FLAGS = []

    configs.GTEST_MAIN_TARGET = None # "testing/gtest/gtest_with_glog_main"

    configs.SYS_STD_HEADERS = set(std_headers.STD_HEADERS) | set(std_headers.SYSTEM_HEADERS)

    configs.CUSTOM_HEADER_IDENTIFICATION_HANDLER = customHeaderIdentificationHandler

    # DepG doesn't recompute the deps of a C++ source file if the content of file have not changed.
    # However if it is supposed to depend on external factors (for example change in header-prefix
    # declaration of third-party targets), we would like to re-generate it.
    # In that case we must compute the checksum of those dependency content and
    # set to `configs.DEPG_DEPS_CACHE_CHECKSUM`.
    configs.DEPG_DEPS_CACHE_CHECKSUM = None

    return configs
