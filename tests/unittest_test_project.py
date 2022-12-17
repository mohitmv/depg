#! /usr/bin/env python3

import unittest
import subprocess
import os
import shutil


PROJECT1_DIR1_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppSource(
    name = "f2",
    hdrs = [ "f2.hpp" ],
    srcs = [ "f2.cpp" ],
    private_deps = [ ":f1" ])

CppSource(
    name = "f1",
    hdrs = [ "f1.hpp" ],
    srcs = [ "f1.cpp" ])

CppExecutable(
    name = "main1",
    srcs = [ "main1.cpp" ],
    private_deps = [ ":f1",
                     ":f2" ])

"""

PROJECT2_DIR1_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppSource(
    name = "f1",
    hdrs = [ "f1.hpp" ],
    srcs = [ "f1.cpp" ])

CppSource(
    name = "f2",
    hdrs = [ "f2.hpp" ],
    srcs = [ "f2.cpp" ],
    private_deps = [ ":f1" ])

CppSource(
    name = "f3",
    hdrs = [ "f3.hpp" ],
    srcs = [ "f3.cpp" ],
    private_deps = [ ":f2" ])

"""

PROJECT2_DIR2_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppSource(
    name = "f1",
    hdrs = [ "f1.hpp" ],
    srcs = [ "f1.cpp" ],
    private_deps = [ "dir1:f1" ])

CppSource(
    name = "f2",
    hdrs = [ "f2.hpp" ],
    srcs = [ "f2.cpp" ],
    private_deps = [ ":f1" ])

CppSharedLib(
    name = "shared_lib",
    hdrs = [ "shared_lib.hpp" ],
    srcs = [ "shared_lib.cpp" ],
    private_deps = [ ":f1",
                     ":f2",
                     "common:common_stuff" ])

"""

PROJECT2_DIR_MAIN_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppExecutable(
    name = "main1",
    srcs = [ "main1.cpp" ],
    private_deps = [ "dir1:f2",
                     "dir1:f3" ])

CppExecutable(
    name = "main2",
    srcs = [ "main2.cpp" ],
    private_deps = [ "dir1:f2",
                     "dir2:shared_lib" ])

"""

PROJECT2_COMMON_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppSource(
    name = "common_stuff",
    hdrs = [ "common_stuff.h" ],
    srcs = [ "common_stuff.cpp" ])

"""



PROJECT4_DIR1_BUILD = """\
#! /usr/bin/env python3

# Semi Auto-generated file ; Don't edit ; Learn more at docs/depg.md

CppSource(
    name = "f1",
    hdrs = [ "f1.hpp" ],
    srcs = [ "f1.cpp" ],
    private_deps = [ "third_party:libB" ])

CppSource(
    name = "f2",
    hdrs = [ "f2.hpp" ],
    srcs = [ "f2.cpp" ],
    private_deps = [ ":f1" ])

CppExecutable(
    name = "main1",
    srcs = [ "main1.cpp" ],
    private_deps = [ ":f1",
                     ":f2" ])

"""

def cmdOutput(cmd):
  return subprocess.check_output(cmd, shell=True).decode("utf-8")

def readFile(fn):
  with open(fn) as fd:
    return fd.read()

def writeFile(fn, content):
  with open(fn, 'w') as fd:
    return fd.write(content)

def replaceTargetType(content, target_name, old_type, new_type):
    tmp = content.split(f'"{target_name}"', 1)
    assert len(tmp) == 2
    tmp0 = new_type.join(tmp[0].rsplit(old_type, 1))
    return tmp0 + f'"{target_name}"' + tmp[1]

def deleteIfExists(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    if os.path.isfile(path):
        os.remove(path)


class TestProject1(unittest.TestCase):
    build_files = ["dir1/BUILD"]
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project1")

    def assertClean(self):
        for build_file in self.build_files:
            self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/{build_file}"))
        self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{self.PROJECT_DIR}/{build_file}"))

    def clean(self):
        for build_file in self.build_files:
            deleteIfExists(f"{self.PROJECT_DIR}/{build_file}")
        deleteIfExists(f"{self.PROJECT_DIR}/build")

    def setUp(self):
        self.clean()
        return

    def tearDown(self):
        self.clean()

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertExists()
        content2 = readFile(f"{self.PROJECT_DIR}/dir1/BUILD")
        content2 = replaceTargetType(content2, "main1", "CppSource", "CppExecutable")
        writeFile(f"{self.PROJECT_DIR}/dir1/BUILD", content2)
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir1/BUILD"), content2)
        self.assertEqual(PROJECT1_DIR1_BUILD, content2)


class TestProject2(unittest.TestCase):
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project2")
    build_files = ["dir1/BUILD", "dir2/BUILD", "dir_main/BUILD", "common/BUILD"]

    def assertClean(self):
        for build_file in self.build_files:
            self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/{build_file}"))
        self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{self.PROJECT_DIR}/{build_file}"))

    def clean(self):
        for build_file in self.build_files:
            deleteIfExists(f"{self.PROJECT_DIR}/{build_file}")
        deleteIfExists(f"{self.PROJECT_DIR}/build")

    def setUp(self):
        self.clean()
        return

    def tearDown(self):
        self.clean()

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertExists()
        content1 = readFile(f"{self.PROJECT_DIR}/dir_main/BUILD").replace("CppSource", "CppExecutable")
        content2 = readFile(f"{self.PROJECT_DIR}/dir2/BUILD")
        content2 = replaceTargetType(content2, "shared_lib", "CppSource", "CppSharedLib")
        writeFile(f"{self.PROJECT_DIR}/dir_main/BUILD", content1)
        writeFile(f"{self.PROJECT_DIR}/dir2/BUILD", content2)
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir_main/BUILD"), content1)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir2/BUILD"), content2)
        self.assertEqual(content1, PROJECT2_DIR_MAIN_BUILD)
        self.assertEqual(content2, PROJECT2_DIR2_BUILD)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/common/BUILD"), PROJECT2_COMMON_BUILD)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir1/BUILD"), PROJECT2_DIR1_BUILD)


class TestProject3(unittest.TestCase):
    build_files = ["dir1/BUILD"]
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project3")

    def assertClean(self):
        self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{self.PROJECT_DIR}/{build_file}"))

    def clean(self):
        if os.path.isdir(f"{self.PROJECT_DIR}/build"):
            shutil.rmtree(f"{self.PROJECT_DIR}/build")

    def setUp(self):
        self.clean()
        return

    def tearDown(self):
        self.clean()
        return

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertExists()
        content2 = readFile(f"{self.PROJECT_DIR}/dir1/BUILD")
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir1/BUILD"), content2)


def makeToolchain(path, libs_map):
    for lib, (hdr, src) in libs_map.items():
        lib_path = f"{path}/{lib}"
        os.makedirs(f"{lib_path}/include/{lib}", exist_ok=True)
        os.makedirs(f"{lib_path}/lib64/", exist_ok=True)
        writeFile(f"{lib_path}/include/{lib}/{lib}.hpp", hdr)
        writeFile(f"{lib_path}/lib64/main.cpp", src)
        os.system(f"g++ -c {lib_path}/lib64/main.cpp -o {lib_path}/lib64/{lib}.o")


class TestProject4(unittest.TestCase):
    build_files = ["dir1/BUILD"]
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project4")
    TOOLCHAIN_PATH = "/tmp/toolchain/depg_test_project4"

    def assertClean(self):
        self.assertFalse(os.path.exists(f"{self.PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{self.PROJECT_DIR}/{build_file}"))

    def clean(self):
        if os.path.isdir(f"{self.PROJECT_DIR}/build"):
            shutil.rmtree(f"{self.PROJECT_DIR}/build")
        if os.path.isdir(self.TOOLCHAIN_PATH):
            shutil.rmtree(self.TOOLCHAIN_PATH)

    def setUp(self):
        self.clean()
        return

    def tearDown(self):
        return
        self.clean()

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        makeToolchain(self.TOOLCHAIN_PATH, {
            "libA": ("const char* libA();",
                     'const char* libA() { return "libA";}'),
            "libB": ('#include "libA/libA.hpp"\nconst char* libB();',
                     'const char* libB() { return "libB";}'),
            })
        self.assertExists()
        content2 = readFile(f"{self.PROJECT_DIR}/dir1/BUILD")
        self.assertTrue(os.system(f"{self.PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{self.PROJECT_DIR}/dir1/BUILD"), content2)
        self.assertEqual(PROJECT4_DIR1_BUILD, content2)


if __name__ == '__main__':
    unittest.main()
