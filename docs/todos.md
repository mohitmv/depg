## TODOs

6. [P0] Add support and unit tests for target level ccflags, include_paths, link flags.

7. [P0] Add a unit tests around the usage of third_party BUILD file and targets used in main source.

1. [P2] Add support for passing the BUILD file topmost comment via config params.

2. [P2] Add support for passing cmake topmost stuff (version and project name) via config params.

4. [P2] Test out the content in topmost BUILD file (example `gcab.so` decl will be there)

5. [P2] Ensure that the BUILD file content is stable. (use OrderedDict well and sort the targets and deps)


## Dones

3. [Done] Respect the INCLUDE_PATHs while auto-generating BUILD files because we cannot find headers otherwise anyways.

