# #! /usr/bin/env python3

# # pylint: disable=missing-module-docstring,missing-function-docstring

# import os
# import export
# import common


# def main():
#     os.chdir("../ms/ctwik_experimental")
#     dep_gen = depg.Depg()
#     targets = dep_gen.depsCover(["."])
#     export_string = export.getTargetsString(targets)
#     file = "/tmp/targets_dump.py"
#     os.makedirs(os.path.dirname(file), exist_ok=True)
#     common.writeFile(file, export_string)
#     print("All the DepG targets are dumped at %s" % file)

# if __name__ == '__main__':
#     main()
