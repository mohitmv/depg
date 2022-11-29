#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=invalid-name

import os
import hashlib

from .targets import TargetType

CPP_TARGETS = set([TargetType.CPP_SOURCE, TargetType.CPP_EXECUTABLE,
                   TargetType.CPP_SHARED_LIB, TargetType.CPP_STATIC_LIB,
                   TargetType.CPP_TEST])

def toRelativePaths(paths):
    for path in paths:
        yield os.path.relpath(path)

def assertRelativePaths(paths):
    for path in paths:
        assert os.path.relpath(path) == path, "Path %s is not relative" % path

def trimExtensions(value, extensions):
    assert isinstance(extensions, tuple)
    for x in extensions:
        if value.endswith(x):
            return value[:-len(x)]
    assert False, value + " doesn't match with extensions: " + str(extensions)
    return None

def trimExtension(value, extension):
    assert value.endswith(extension)
    return value[:-len(extension)]

def hasExtensions(value, extensions):
    assert isinstance(extensions, tuple)
    for x in extensions:
        if value.endswith(x):
            return True
    return False

def withCache(self_to_cache_store_func):
    """
    Annotation to be used on class members. @self_to_cache_store_func takes
    a function that goes from self -> cache_store. @cache_store is a dict like
    object (should support item getter and setter via  `cache_store[a]=b`
    like syntax). Default dict is also a valid cache_store.
    Note: The class member on which this annotation is applied should be pure
          function. i.e. if the function is called again with the same input,
          it's output must be same.
    """
    def func_converter(old_func):
        def new_func(self, *args):
            cache_store = self_to_cache_store_func(self)
            if cache_store is not None and args in cache_store:
                return cache_store[args]
            output = old_func(self, *args)
            if cache_store is not None:
                cache_store[args] = output
            return output
        return new_func
    return func_converter

def withCacheOnArg0(self_to_cache_store_func):
    """
    Same as withCache annotation, but the cache is applied on only first
    argument of the input. The implementation assumes that:
    For valid inputs of the functions on which this annotation is applied,
    output would be same if the first argument (of inputs) is same.
    i.e. cache is stored corresponding to the first argument of input.
    """
    def func_converter(old_func):
        def new_func(self, arg1, *args):
            cache_store = self_to_cache_store_func(self)
            if cache_store is not None and arg1 in cache_store:
                return cache_store[arg1]
            output = old_func(self, arg1, *args)
            if cache_store is not None:
                cache_store[arg1] = output
            return output
        return new_func
    return func_converter

def withSerializableCacheOnArg0(self_to_cache_store_func, serializer=None,
                                deserializer=None):
    """
    Same as withCache annotation, but the cache is applied on only first
    argument of the input. The implementation assumes that:
    For valid inputs of the functions on which this annotation is applied,
    output would be same if the first argument (of inputs) is same.
    i.e. cache is stored corresponding to the first argument of input.
    """
    def func_converter(old_func):
        def new_func(self, arg1, *args):
            cache_store = self_to_cache_store_func(self)
            if cache_store is not None and arg1 in cache_store:
                output = cache_store[arg1]
                if deserializer is not None:
                    output = deserializer(output)
                return output
            output = old_func(self, arg1, *args)
            if cache_store is not None:
                cache_output = output
                if serializer is not None:
                    cache_output = serializer(output)
                cache_store[arg1] = cache_output
            return output
        return new_func
    return func_converter

def assertFileExists(file, configs, msg=''):
    if file in configs.IGNORE_EXISTANCE:
        return
    assert os.path.isfile(file), msg

def readFile(file):
    with open(file, encoding="utf-8", errors="ignore") as fd:
        return fd.read()

def writeFile(file, data, mode='w'):
    with open(file, mode, encoding="utf-8") as fd:
        return fd.write(data)

def getFileCheckSum(file):
    assert (os.path.isfile(file)), ("File %s doesn't exists." % file)
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
