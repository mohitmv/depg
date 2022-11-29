import os
import shutil
import collections

from . import merge_build_file
from . import target_graph_builder
from . import common
from . import parser
from . import algorithms

from .targets import TargetType

def readBuildFileAndFullTargetPaths(build_file):
    output = collections.OrderedDict()
    directory = os.path.dirname(build_file)
    targets = parser.readBuildFile(build_file)
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

def listBuildFilesRecursive(directory, forbidden_paths, ignored_paths):
    """
    For a given relative path of @directory (w.r.t Git Root),
    list down all the BUILD files in this directory recursively.
    All file paths in the output are also relative w.r.t. Git root.
    Precondition: @directory must exist.

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
    output = []
    for (root, _, _) in os.walk(directory):
        root = os.path.relpath(root)
        if (root in forbidden_paths
                or (root != directory and root in ignored_paths)):
            continue
        build_file = f"{root}/BUILD"
        if os.path.isfile(build_file):
            output.append(build_file)
    return output


def readTargets(target_names_or_dirs, configs):
    build_files_map = {}
    def readBuildFileCached(build_file):
        if build_file not in build_files_map:
            build_files_map[build_file] = readBuildFileAndFullTargetPaths(build_file)
        return build_files_map[build_file]
    target_names = set()
    common.assertRelativePaths(configs.IGNORED_PATHS)
    excluded = target_graph_builder.getAllForbiddenPaths(configs)
    def getTarget(tname, error=''):
        directory = os.path.dirname(tname)
        build_file = f"{directory}/BUILD"
        if not os.path.isfile(build_file):
            assert False, f"File {build_file} not found " + error
        build_file_struct = readBuildFileCached(build_file)
        if tname in build_file_struct:
            return build_file_struct[tname]
        error = f"Target {os.path.basename(tname)} not found in {build_file}" + error
        assert False, error

    for input_target in target_names_or_dirs:
        input_target = os.path.relpath(input_target)
        if os.path.isdir(input_target):
            build_files = listBuildFilesRecursive(input_target, excluded,
                                            configs.IGNORED_PATHS)
            for build_file in build_files:
                build_file_struct = readBuildFileCached(build_file)
                target_names |= set(build_file_struct.keys())
        else:
            target_names.add(input_target.replace(":", "/"))
    def edgeFunc(tname):
        target = getTarget(tname)
        deps = target.get('public_deps', []) + target.get('private_deps', [])
        for dep in deps:
            getTarget(dep, error=f' , used in deps of {tname}')
        return deps
    target_names, cycles = algorithms.topologicalSortedDepsCoverAndCycles(target_names, edgeFunc)
    if len(cycles) > 0:
        print("Found cycles in targets: " + (" -> ".join(cycles[0])))
        exit(1)
    return dict((tname, getTarget(tname)) for tname in target_names)


def mergeListOfList(list_of_list):
    output = []
    [output.extend(x) for x in list_of_list]
    return output


CPP_EXECUTABLE_DEPS_COVER_GO_IN = set([TargetType.CPP_SOURCE, TargetType.NOP_TARGET, TargetType.PROTO_LIBRARY, TargetType.GRPC_LIBRARY])

def combineFields(targets_map, field):
    output = []
    for tname, target in targets_map.items():
        output.extend(target.get(field, []))
    return output

class CMakeFileGen:
    def __init__(self, configs, targets_map):
        self.configs = configs
        self.targets_map = targets_map
        self.cmake_i_deps_map = {}
        self.cmake_decl = []

    def makeCMakeDecl(self):
        self.makeCMakeMetaDecl()
        self.makeCMakeTargetDecl()
        return self.cmake_decl

    def makeCMakeMetaDecl(self):
        if self.configs.INCLUDE_PATHS:
            self.cmake_decl.append(("include_directories", (self.configs.INCLUDE_PATHS)))

    def makeCMakeTargetDecl(self):
        for _, target in self.targets_map.items():
            if target.type == TargetType.CPP_SOURCE:
                self.handleCppSource(target)
            elif target.type in [TargetType.CPP_EXECUTABLE, TargetType.CPP_TEST]:
                self.handleCppExecutable(target)
            elif target.type in [TargetType.PROTO_LIBRARY, TargetType.GRPC_LIBRARY]:
                self.handleProtoLibrary(target)
            else:
                assert False, target

    def handleProtoLibrary(self, target):
        self.cmake_i_deps_map[target.name] = []

    def handleCppSource(self, target):
        cmake_i_deps = []
        if "srcs" in target:
            cmake_tname = target.name.replace("/", "_")
            elms = [cmake_tname, "OBJECT"]
            elms.extend(target.srcs)
            public_deps_map = self.publicDepsCoverTargetMap(target["name"])
            cc_flags = combineFields(public_deps_map, "public_cc_flags") + target.get("private_cc_flags", [])
            self.cmake_decl.append(("add_library", elms))
            cmake_i_deps.append(cmake_tname)
        if "library" in target:
            cmake_i_deps.append(target.library)
        self.cmake_i_deps_map[target.name] = cmake_i_deps

    def handleCppExecutable(self, target):
        cmake_tname = target["name"].replace("/", "_")
        self.cmake_decl.append(("add_executable", [cmake_tname] + target["srcs"]))
        public_deps_map = self.publicDepsCoverTargetMap(target["name"])
        deps_map = self.depsCoverTargetMap(target["name"])
        link_flags = combineFields(deps_map, "link_flags")
        cc_flags = combineFields(public_deps_map, "public_cc_flags") + target.get("private_cc_flags", [])
        include_paths = combineFields(public_deps_map, "public_include_paths") + target.get("private_include_paths", [])
        elms = [cmake_tname]
        [elms.extend(self.cmake_i_deps_map[tname]) for tname, x in deps_map.items() if tname != target.name]
        elms.extend(link_flags)
        self.cmake_i_deps_map[target.name] = [cmake_tname]
        if len(elms) > 1:
            self.cmake_decl.append(("target_link_libraries", elms))

    def depsCoverTargetMap(self, tname):
        target_names = algorithms.topologicalSortedDepsCover([tname], self.cppDepsCoverEdgeFunc)
        return collections.OrderedDict((x, self.targets_map[x]) for x in target_names)

    def publicDepsCoverTargetMap(self, tname):
        # Even for public deps, start with all direct deps.
        target_names = algorithms.topologicalSortedDepsCover(
                self.cppDepsCoverEdgeFunc(tname), self.cppPublicDepsCoverEdgeFunc)
        return collections.OrderedDict((x, self.targets_map[x]) for x in target_names)

    def filterDepsInCppDepsCoverPath(self, deps):
        return [dep for dep in deps if self.targets_map[dep].type in CPP_EXECUTABLE_DEPS_COVER_GO_IN]

    def cppPublicDepsCoverEdgeFunc(self, tname):
        target = self.targets_map[tname]
        deps = target.get("public_deps", [])
        return self.filterDepsInCppDepsCoverPath(deps)

    def cppDepsCoverEdgeFunc(self, tname):
        target = self.targets_map[tname]
        deps = target.get("public_deps", []) + target.get("private_deps", [])
        return self.filterDepsInCppDepsCoverPath(deps)


def unparseCmakeDecl(cmake_decl, project_name="x"):
    output = "cmake_minimum_required(VERSION 3.1)\n"
    output += f"project({project_name})\n"
    for (name, args) in cmake_decl:
        output += f"{name}({' '.join(args)})\n"
    return output


def genCmake(targets_n_dirs, configs, cmake_build_dir):
    targets_map = readTargets(targets_n_dirs, configs)
    cmake_file_gen = CMakeFileGen(configs, targets_map)
    os.makedirs(cmake_build_dir, exist_ok=True)
    cmake_decl = cmake_file_gen.makeCMakeDecl()
    cmake_file_content = unparseCmakeDecl(cmake_decl)
    for top_dir in configs.TOP_DIRECTORY_LIST:
        if os.path.exists(f"{cmake_build_dir}/{top_dir}"):
            os.unlink(f"{cmake_build_dir}/{top_dir}")
        os.symlink(f"../{top_dir}", f"{cmake_build_dir}/{top_dir}")
    common.writeFile(f"{cmake_build_dir}/CMakeLists.txt", cmake_file_content)
