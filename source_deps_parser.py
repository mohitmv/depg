#! /usr/bin/env python3

"""
Source Deps Parser
"""

# pylint: disable=line-too-long,missing-module-docstring
# pylint: disable=too-many-instance-attributes,invalid-name
# pylint: disable=missing-function-docstring,too-many-return-statements
# pylint: disable=missing-class-docstring,too-many-branches

import re
import os

from . import common
from .targets import TargetType

def rstripSlashFromKeys(d):
    return dict((k.rstrip("/"), v) for k, v in d.items())

def cppHeaderRegexList():
    re1 = re.compile("^[ ]*#[ ]*include[ ]*<([^>]+)>", flags=re.MULTILINE)
    re2 = re.compile("^[ ]*#[ ]*include[ ]*\"([^\"]+)\"", flags=re.MULTILINE)
    return (re1, re2)

def protoImportRegex():
    regex = re.compile("^[ ]*import[ ]+\"([^\"]+)\"", flags=re.MULTILINE)
    return regex

def thriftIncludeRegex():
    regex = re.compile("^[ ]*include[ ]+\"([^\"]+)\"", flags=re.MULTILINE)
    return regex

def getCppHeader(file, header_regex_list):
    content = common.readFile(file)
    return tuple(list(regex.findall(content)) for regex in header_regex_list)

def getProtoImports(file, regex):
    return list(regex.findall(common.readFile(file)))

def getThriftIncludes(file, regex):
    return list(regex.findall(common.readFile(file)))

def DeserializeTargets(targets):
    for target in targets:
        target['type'] = TargetType(target['type'])
    return targets

def withCache(cache_store_func):
    return common.withSerializableCacheOnArg0(cache_store_func,
                                              deserializer=DeserializeTargets)

class SourceDepsParser:
    def __init__(self, system_includes, header_prefixes_map,
                 manual_header_interpreter, source_file_to_deps_cache,
                 configs):
        self.system_includes = set(system_includes)
        self.header_prefixes_map = rstripSlashFromKeys(header_prefixes_map)
        self.cpp_header_regex_list = cppHeaderRegexList()
        self.manual_header_interpreter = manual_header_interpreter
        self.header_to_target_cache = {}
        self.thrift_parser_regex = thriftIncludeRegex()
        self.proto_parser_regex = protoImportRegex()
        self.source_file_to_deps_cache = source_file_to_deps_cache
        self.configs = configs

    @withCache(lambda self: self.source_file_to_deps_cache)
    def cppSourceToDeps(self, source_file):
        headers_bkt = getCppHeader(source_file, self.cpp_header_regex_list)
        headers = headers_bkt[0] + headers_bkt[1]
        return self.__cppHeadersToTargets(headers, source_file)

    @withCache(lambda self: self.source_file_to_deps_cache)
    def protoSourceToDeps(self, source_file):
        imports = getProtoImports(source_file, self.proto_parser_regex)
        public_deps = []
        for dep_name in imports:
            if dep_name.startswith("google/protobuf/"):
                continue
            common.assertFileExists(
                dep_name,
                self.configs,
                "'%s' doesn't exists. Required by %s" % (dep_name, source_file))
            public_deps.append(dict(name=dep_name,
                             type=TargetType.PROTO_LIBRARY))
        return public_deps

    @common.withCacheOnArg0(lambda self: self.header_to_target_cache)
    def __cppHeaderToTarget(self, header, source_file):
        if header in self.system_includes:
            return None
        configs = self.configs
        if header.endswith(configs.GRPC_HEADER_EXTENSION):
            target = common.trimExtension(header, configs.GRPC_HEADER_EXTENSION)
            common.assertFileExists(target + configs.PROTO_EXTENSION, self.configs)
            return dict(
                type=TargetType.GRPC_LIBRARY,
                name=target + ".grpc",
                deps=[target + configs.PROTO_EXTENSION])
        if header.endswith(configs.PROTO_HEADER_EXTENSION):
            target = header[:-len(configs.PROTO_HEADER_EXTENSION)] + configs.PROTO_EXTENSION
            if os.path.isfile(target):
                return dict(
                    type=TargetType.PROTO_LIBRARY,
                    name=target)
        if common.hasExtensions(header, configs.CPP_HEADER_EXTENSIONS):
            if not os.path.isfile(header):
                full_path_header = os.path.relpath(os.path.join(
                    os.path.dirname(source_file), header))
                if os.path.isfile(full_path_header):
                    header = full_path_header
            if os.path.isfile(header):
                return dict(
                    type=TargetType.CPP_SOURCE,
                    name=common.trimExtensions(
                        header, configs.CPP_HEADER_EXTENSIONS))
        thirdp_target = self.__getThirdPartyCppLibraryTarget(header)
        if thirdp_target is not None:
            return dict(
                type=TargetType.CPP_SOURCE,
                name=thirdp_target)
        if header in configs.IGNORED_HEADERS:
            return None
        obj = self.manual_header_interpreter(header)
        if obj is not None:
            return obj
        raise Exception(
            "Unrecognized Header '%s' in file '%s'" % (header, source_file))

    def __cppHeadersToTargets(self, headers, source_file):
        output = []
        deps_names = set()
        for header in headers:
            target = self.__cppHeaderToTarget(header, source_file)
            if target is not None and target['name'] not in deps_names:
                output.append(target)
                deps_names.add(target['name'])
        return output

    def __getThirdPartyCppLibraryTarget(self, header):
        for i in range(header.count("/") + 1):
            header_p = header.rsplit('/', i)[0]
            if header_p in self.header_prefixes_map:
                return self.header_prefixes_map[header_p]
        return None
