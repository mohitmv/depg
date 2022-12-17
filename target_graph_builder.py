#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=missing-class-docstring,too-many-return-statements
# pylint: disable=invalid-name

import os
import json
from collections import OrderedDict

from . import algorithms
from . import common
from . import utils
from .targets import TargetType, DepgTarget
from .source_deps_parser import SourceDepsParser
from . import cache


GTEST_MAIN_TARGET = None # "testing/gtest/gtest_with_glog_main"

import time
DEPG_VERSION_VALUE = int(time.time() * 100)

def combinedList(a, b):
    if len(a) == 0:
        return b
    if len(b) == 0:
        return a
    return a + b


def fileToTarget(file, configs):
    if common.hasExtensions(file, configs.CPP_EXTENSIONS):
        return common.trimExtensions(file, configs.CPP_EXTENSIONS)
    if file.endswith(configs.PROTO_EXTENSION):
        return file
    return None


def listDirectoryRecursive(directory, forbidden_paths, ignored_paths):
    """
    For a given relative path of @directory (w.r.t Git Root),
    list down all the files in this directory recursively.
    All file paths in the output are also relative w.r.t. Git root.
    returns [@directory] if the @directory doesn't exists but file exists.
    returns [] if the @directory doesn't exists.

    The directories matching with @forbidden_paths are not visited. No
    forbidden file will be present in output list.

    Similar to @forbidden_paths, the directories matching with @ignored_paths
    are also not visited unless explicitly asked.
    For example let [`a/b`, 'a/c'] are the @ignored_paths but if client query
    listDirectoryRecursive('a/b/q', ...) then all files in directory `a/b/q`
    will be returned even if directory `a/b` was ignored. However if the client
    query `listDirectoryRecursive('a', ...)` then `a/b`, `a/c` won't be visited.

    Note that if [`a/b`, 'a/c'] are the forbidden_paths then result of
    listDirectoryRecursive('a/b/q', ...) will be [].

    Let a path is a valid relative path iff `os.path.relpath(path) == path`

    Preconditions:
    1. @directory is a valid relative path.
    2. @forbidden_paths and @ignored_paths are valid relative paths.

    """
    assert os.path.relpath(directory) == directory
    for i in forbidden_paths:
        if directory.startswith(i):
            return []
    if os.path.isfile(directory):
        # Assert (@directory not in @forbidden_paths)
        return [directory]
    output = []
    for (root, dirs, files) in os.walk(directory):
        root = os.path.relpath(root)
        if (root in forbidden_paths
                or (root != directory and root in ignored_paths)):
            dirs[:] = []
            continue
        for file in files:
            file_path = root + "/" + file
            if file_path in forbidden_paths:
                continue
            output.append(file_path)
    return output


def changedPathsToTargetNames(input_paths, configs):
    """
    Given a list of files or directory (i.e. paths), return the list of target
    names corresponding to those files. When directories are given in input,
    all files of those directories are considered recursively.

    Note: If a files is unknown to DepG, i.e. it doesn't correspond to any
    target then that file will be silently ignored.

    Paths specified in @excluded_paths are ignored.
    All the forbidden paths of DepG are also ignored.

    Preconditions : Each of the path in @input_paths must exists and should be
                    relative w.r.t git-root.
    """
    common.assertRelativePaths(configs.IGNORED_PATHS)
    common.assertRelativePaths(configs.FORBIDDEN_PATHS)
    files = utils.OrderedSet()
    for path in input_paths:
        path = os.path.relpath(path)
        if os.path.isfile(path):
            if path not in configs.FORBIDDEN_PATHS:
                files.add(path)
        else:
            assert os.path.isdir(path)
            new_files = listDirectoryRecursive(
                path, configs.FORBIDDEN_PATHS, configs.IGNORED_PATHS)
            [files.add(x) for x in new_files]
    output = utils.OrderedSet()
    for file in files:
        target = fileToTarget(file, configs)
        if target is not None:
            output.add(target)
    return list(output)


def getCacheFile(cache_directory):
    return cache_directory.rstrip("/") + "/cache.json"


def loadCacheData(file):
    if os.path.isfile(file):
        content = common.readFile(file).strip()
        if len(content) > 0:
            return json.loads(content)
    return {}

def loadCache(configs):
    if configs.CACHE_DIRECTORY:
        data = loadCacheData(getCacheFile(configs.CACHE_DIRECTORY))
        # DepG version is used for invalidating the entire cache when we make some
        # change in the DepG software itself.
        # If you make some change in DepG software, you are expected to increase the
        # DEPG_VERSION_VALUE counter by 1.
        DEPG_VERSION_KEY = '__DEPG_VERSION__'
        DEPG_DEPS_CACHE_CHECKSUM = "DEPG_DEPS_CACHE_CHECKSUM"
        if data.get(DEPG_VERSION_KEY) != DEPG_VERSION_VALUE or \
                data.get(DEPG_DEPS_CACHE_CHECKSUM) != configs.DEPG_DEPS_CACHE_CHECKSUM:
            data = {
                DEPG_VERSION_KEY : DEPG_VERSION_VALUE,
                DEPG_DEPS_CACHE_CHECKSUM : configs.DEPG_DEPS_CACHE_CHECKSUM
            }
        return cache.InMemoryFileValueCache(data)
    return None


def storeCache(cache_directory, cache_object):
    if cache_directory is None:
        return
    file = getCacheFile(cache_directory)
    os.makedirs(os.path.dirname(file), exist_ok=True)
    common.writeFile(file, json.dumps(cache_object.export()))

class TargetGraphBuilder:
    def __init__(self, configs):
        self.configs = configs
        self.source_deps_cache = loadCache(configs)
        self.source_deps_parser = SourceDepsParser(
            configs.SYS_STD_HEADERS, configs.HEADER_PREFIXES_MAP,
            configs.CUSTOM_HEADER_IDENTIFICATION_HANDLER,
            self.source_deps_cache, configs)
        self.target_map = {}
        self.edge_cache = {}

    def depsCover(self, target_names):
        for target_name in target_names:
            self.declareTarget(target_name,
                               type=self.getTargetType(target_name))
        cover = algorithms.depsCover(target_names, self.edgeFunc)
        target_map = dict((tname, self.target_map[tname]) for tname in cover)
        self.target_map = target_map
        storeCache(self.configs.CACHE_DIRECTORY, self.source_deps_cache)
        return target_map

    def getDeps(self, target_names):
        """
        Given a list of target names, return a map which contains
        target-definiton for given target names.
        Note that returned map might have more keys than @target_names because
        it also contains the target-declaration for the targets in the deps of
        @target_names. Note that "target-declaration" info only contains the
        type and name of that target. No additional information. These info
        can be used for checking the target_type of any deps of any target
        from @target_names.
        """
        for target_name in target_names:
            self.declareTarget(target_name,
                               type=self.getTargetType(target_name))
            self.edgeFunc(target_name)
        storeCache(self.configs.CACHE_DIRECTORY, self.source_deps_cache)
        return self.target_map

    def getTargetType(self, target_name, parent_target_name=None):
        """
        Given a @target_name, return the target type. In case of invalid
        @target_name, raise DepgError.
        """
        if target_name in self.target_map:
            return self.target_map[target_name].type
        # if target_name in self.manually_declared_targets:
        #     return self.manually_declared_targets[target_name].type
        if target_name.endswith(self.configs.PROTO_EXTENSION):
            return TargetType.PROTO_LIBRARY
        for e in self.configs.CPP_EXTENSIONS:
            file = target_name + e
            if os.path.isfile(file):
                if file.endswith(self.configs.TEST_FILE_EXTENSION):
                    return TargetType.CPP_TEST
                return TargetType.CPP_SOURCE
        error = "Unable to recognize the target '%s' " % target_name
        if parent_target_name:
            error += " in the deps of '%s' " % parent_target_name
        assert False, error
        return None

    def declareTargets(self, target_decls):
        for target_decl in target_decls:
            self.declareTarget(**target_decl)

    def declareTarget(self, name, **kwargs):
        """
        Declare a target with minimal information we know about target.
        If the target already exists, do nothing.
        """
        if name in self.target_map:
            return
        assert 'type' in kwargs
        self.target_map[name] = DepgTarget(name=name, **kwargs)

    def buildTargetFromSource(self, target):
        """
        Populate the fields of @target by inspecting the source code.
        Precondition: Target should be already declared (i.e. name and type must
                      be already populated).
        """
        if target.type in common.CPP_TARGETS:
            self.buildCppTarget(target)
        elif target.type == TargetType.PROTO_LIBRARY:
            self.buildProtoTarget(target)
        elif target.type == TargetType.GRPC_LIBRARY:
            self.buildGrpcTarget(target)
        else:
            assert False, (f"Unknown target {target.name} {target.type.name}")

    def buildTarget(self, target):
        """
        Build the properties of an already declared @target. This method
        populates the target fields eg: 'header', 'srcs', 'public_deps'.. etc.
        Assume: It method should be called at most once per target.
        """
        self.buildTargetFromSource(target)
        deps = target.get('public_deps', []) + target.get('private_deps', [])
        for dep_name in deps:
            target_type = self.getTargetType(dep_name, target.name)
            self.declareTarget(dep_name, type=target_type)

    def cppSourceToDeps(self, source_file, target_name):
        deps_list = self.source_deps_parser.cppSourceToDeps(source_file)
        deps_list = [d for d in deps_list if d['name'] != target_name]
        for dep in deps_list:
            self.declareTarget(**dep)
        return [dep['name'] for dep in deps_list]

    def cppSourcesToDeps(self, source_files, target_name):
        output = []
        for source_file in source_files:
            output.extend(self.cppSourceToDeps(source_file, target_name))
        return output

    def buildCppTarget(self, target):
        """
        Populate the fields of C++ @target by inspecting the source code.
        Precondition: Target should be already declared (i.e. name and type must
                      be already populated).
        """
        configs = self.configs
        if "hdrs" not in target:
            hdrs = []
            for x in configs.CPP_HEADER_EXTENSIONS:
                if os.path.isfile(target.name + x):
                    hdrs.append(target.name + x)
            if len(hdrs) > 0:
                target.hdrs = hdrs
        if "srcs" not in target:
            for x in configs.CPP_SOURCE_EXTENSIONS:
                if os.path.isfile(target.name + x):
                    target.srcs = [target.name + x]
                    break
        public_deps_set = set()
        if "hdrs" in target:
            public_deps = self.cppSourcesToDeps(target.hdrs, target.name)
            if len(public_deps) > 0:
                target.public_deps = public_deps
                public_deps_set = set(target.public_deps)
        if "srcs" in target:
            private_deps = []
            if target.type == TargetType.CPP_TEST:
                if configs.GTEST_MAIN_TARGET is not None:
                    if configs.GTEST_MAIN_TARGET not in self.target_map:
                        self.declareTarget(name=configs.GTEST_MAIN_TARGET,
                                           type=TargetType.CPP_SOURCE)
                    private_deps.append(configs.GTEST_MAIN_TARGET)
            private_deps.extend(self.cppSourcesToDeps(
                target.srcs, target.name))
            private_deps = [x for x in private_deps if x not in public_deps_set]
            if len(private_deps) > 0:
                target.private_deps = private_deps

    def buildProtoTarget(self, target):
        deps_list = self.source_deps_parser.protoSourceToDeps(target.name)
        for dep in deps_list:
            self.declareTarget(**dep)
        target.public_deps = [dep['name'] for dep in deps_list]

    def buildGrpcTarget(self, target):
        pass

    @common.withCacheOnArg0(lambda self: self.edge_cache)
    def edgeFunc(self, target_name):
        assert target_name in self.target_map
        target = self.target_map[target_name]
        self.buildTarget(target)
        return target.get('private_deps', []) + target.get('public_deps', [])
