#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=invalid-name

import os

from . import common


def getFileTimestampMs(file):
    a = os.path.getmtime(file)
    return int(a*1000)

class InMemoryFileValueCache:
    """In memory cache from file content to value."""
    def __init__(self, cache_dump=None):
        self.data = cache_dump or {}

    def export(self):
        return self.data

    def __contains__(self, file):
        if file not in self.data:
            return False
        value = self.data[file]
        if getFileTimestampMs(file) == value['timestamp']:
            return True
        if common.getFileCheckSum(file) == value['checksum']:
            return True
        return False

    def __getitem__(self, file):
        assert self.__contains__(file)
        return self.data[file]['value']

    def __setitem__(self, file, value):
        self.data[file] = dict(
            timestamp=getFileTimestampMs(file),
            checksum=common.getFileCheckSum(file),
            value=value)
