#! /usr/bin/env python3

import unittest
import subprocess
import os
import shutil

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project1")

EXPECTED_MAIN1_OUTPUT="""\
START dir1_f2
dir1_f1
END dir1_f2
START dir1_f3
START dir1_f2
dir1_f1
END dir1_f2
END dir1_f3
"""

def cmdOutput(cmd):
  return subprocess.check_output(cmd, shell=True).decode("utf-8")

def readFile(fn):
  with open(fn) as fd:
    return fd.read()

def writeFile(fn, content):
  with open(fn, 'w') as fd:
    return fd.write(content)

class TestProject1(unittest.TestCase):
    build_files = ["dir1/BUILD", "dir2/BUILD", "dir_main/BUILD"]

    def assertClean(self):
        for build_file in self.build_files:
            self.assertFalse(os.path.exists(f"{PROJECT_DIR}/{build_file}"))
        self.assertFalse(os.path.exists(f"{PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{PROJECT_DIR}/{build_file}"))

    def clean(self):
        for build_file in self.build_files:
            if os.path.isfile(f"{PROJECT_DIR}/{build_file}"):
                os.remove(f"{PROJECT_DIR}/{build_file}")
        if os.path.isdir(f"{PROJECT_DIR}/build"):
            shutil.rmtree(f"{PROJECT_DIR}/build")

    def tearDown(self):
        self.clean()

    def test_main(self):
        self.assertClean()
        os.system(f"{PROJECT_DIR}/tools/depg_main.py .")
        self.assertExists()
        content = readFile(f"{PROJECT_DIR}/dir_main/BUILD").replace("CppSource", "CppExecutable")
        writeFile(f"{PROJECT_DIR}/dir_main/BUILD", content)
        os.system(f"{PROJECT_DIR}/tools/depg_main.py .")
        self.assertEqual(readFile(f"{PROJECT_DIR}/dir_main/BUILD"), content)
        os.system(f"{PROJECT_DIR}/tools/depg_main.py . --gen_cmake")
        self.assertTrue(os.path.isfile(f"{PROJECT_DIR}/build/CMakeLists.txt"))
        os.chdir(f"{PROJECT_DIR}/build")
        self.assertTrue(os.system("cmake . && make") == 0)
        self.assertEqual(cmdOutput("./dir_main_main1"), EXPECTED_MAIN1_OUTPUT)
        

if __name__ == '__main__':
    unittest.main()
