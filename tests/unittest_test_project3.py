#! /usr/bin/env python3

import unittest
import subprocess
import os
import shutil

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project3")

EXPECTED_MAIN1_OUTPUT = """\
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
    build_files = ["dir1/BUILD"]

    def assertClean(self):
        self.assertFalse(os.path.exists(f"{PROJECT_DIR}/build"))

    def assertExists(self):
        for build_file in self.build_files:
            self.assertTrue(os.path.isfile(f"{PROJECT_DIR}/{build_file}"))

    def clean(self):
        if os.path.isdir(f"{PROJECT_DIR}/build"):
            shutil.rmtree(f"{PROJECT_DIR}/build")

    def setUp(self):
        self.clean()
        return

    def tearDown(self):
        return
        self.clean()

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertExists()
        content2 = readFile(f"{PROJECT_DIR}/dir1/BUILD")
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{PROJECT_DIR}/dir1/BUILD"), content2)
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py . --gen_cmake") == 0)
        self.assertTrue(os.path.isfile(f"{PROJECT_DIR}/build/CMakeLists.txt"))
        os.chdir(f"{PROJECT_DIR}/build")
        self.assertTrue(os.system("cmake . && make") == 0)
        self.assertEqual(cmdOutput("./dir1_main1"), EXPECTED_MAIN1_OUTPUT)

if __name__ == '__main__':
    unittest.main()
