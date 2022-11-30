#! /usr/bin/env python3

import unittest
import subprocess
import os
import shutil

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__) + "/test_project1")

EXPECTED_MAIN1_OUTPUT = """\
START dir1_main
dir1_f1
START dir1_f2
dir1_f1
END dir1_f2
END dir1_main
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

class TestProject1(unittest.TestCase):
    build_files = ["dir1/BUILD"]

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

    def setUp(self):
        return
        self.clean()

    def tearDown(self):
        self.clean()
        return

    def test_main(self):
        self.assertClean()
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertExists()
        content2 = readFile(f"{PROJECT_DIR}/dir1/BUILD")
        content2 = replaceTargetType(content2, "main1", "CppSource", "CppExecutable")
        writeFile(f"{PROJECT_DIR}/dir1/BUILD", content2)
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py .") == 0)
        self.assertEqual(readFile(f"{PROJECT_DIR}/dir1/BUILD"), content2)
        self.assertTrue(os.system(f"{PROJECT_DIR}/tools/depg_main.py . --gen_cmake") == 0)
        self.assertTrue(os.path.isfile(f"{PROJECT_DIR}/build/CMakeLists.txt"))
        os.chdir(f"{PROJECT_DIR}/build")
        self.assertTrue(os.system("cmake . && make") == 0)
        self.assertEqual(cmdOutput("./dir1_main1"), EXPECTED_MAIN1_OUTPUT)

if __name__ == '__main__':
    unittest.main()
