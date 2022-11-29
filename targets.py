#! /usr/bin/env python3

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=missing-class-docstring

import os
from enum import IntEnum

class TargetType(IntEnum):
    CPP_SOURCE = 1 # Any x.cpp file.
    CPP_EXECUTABLE = 2 # One of the deps or source must include `int main(...)`
    CPP_TEST = 3
    CPP_SHARED_LIB = 4
    CPP_STATIC_LIB = 5
    NOP_TARGET = 7
    PROTO_LIBRARY = 8
    GRPC_LIBRARY = 9
    CUSTOM = 10
    def funcName(self):
        return self.name.title().replace("_", "")

class TargetTag(IntEnum):
    THIRD_PARTY = 1

class DepgError(Exception):
    pass

class DepgRulesFactory:
    all_rules = dict()
    all_updates = dict()
    @staticmethod
    def reset():
        DepgRulesFactory.all_rules = dict()
        DepgRulesFactory.all_updates = dict()


class DepgTarget(dict):
    def __init__(self, initial_value=None, **kwargs):
        self.__dict__ = self
        dict.__init__(self, (initial_value or {}), **kwargs)


class RuleDeclaration:
    def __init__(self, depg_rules, rule_type):
        self.depg_rules = depg_rules
        self.prefix = depg_rules.prefix
        self.rule_type = rule_type

    def __call__(self, name, **kwargs):
        full_name = os.path.join(self.prefix, name)
        if self.depg_rules.hasTarget(full_name):
            raise DepgError("Found multiple targets with name '{0}' in {1}"
                            .format(full_name, self.prefix))
        new_list = []
        for dep in kwargs.get("deps", []):
            assert dep.strip() == dep, \
                ("Extra whitespace in dep '%s' of '%s'." % (dep, full_name))
            assert len(dep) > 0, "Invalid dep '%s' of '%s'" % (dep, full_name)
            if dep[0] == ':':
                new_value = os.path.join(self.prefix, dep[1:])
            else:
                new_value = dep.replace(":", "/")
            new_list.append(new_value)
        kwargs["deps"] = new_list
        self.depg_rules.addTarget(full_name, DepgTarget(
            type=self.rule_type,
            name=full_name,
            **kwargs))

class RuleUpdateDeclaration:
    def __init__(self, depg_updates, rule_type):
        self.depg_updates = depg_updates
        self.prefix = depg_updates.prefix
        self.rule_type = rule_type

    def __call__(self, name, **kwargs):
        full_name = os.path.join(self.prefix, name)
        if self.depg_updates.hasUpdate(full_name):
            raise DepgError("Found multiple updates with name '{0}' in {1}"
                            .format(full_name, self.prefix))
        new_list = []
        for dep in kwargs.get("deps", []):
            assert dep.strip() == dep, \
                ("Extra whitespace in dep '%s' of '%s'." % (dep, full_name))
            assert len(dep) > 0, "Invalid dep '%s' of '%s'" % (dep, full_name)
            if dep[0] == ':':
                new_value = os.path.join(self.prefix, dep[1:])
            else:
                new_value = dep.replace(":", "/")
            new_list.append(new_value)
        kwargs["deps"] = new_list
        self.depg_updates.update(full_name, type=self.rule_type, **kwargs)


class DepgRules:
    def __init__(self, prefix=''):
        self.prefix = prefix
        self.rules = {}
        for target_type in TargetType:
            j = target_type.name.title().replace("_", "")
            self.__dict__[j] = RuleDeclaration(self, target_type)

    def addTarget(self, full_name, target):
        self.rules[full_name] = target

    def hasTarget(self, full_name):
        return full_name in self.rules

class DepgRuleCreater:
    #pylint:disable=non-parent-init-called
    def __init__(self, prefix=''):
        DepgRules.__init__(self, prefix)

    def addTarget(self, full_name, target):
        DepgRulesFactory.all_rules[full_name] = target

    def hasTarget(self, full_name):
        return full_name in DepgRulesFactory.all_rules

class DepgRuleUpdater:
    def __init__(self, prefix=''):
        self.prefix = prefix
        self.rules = {}
        for target_type in TargetType:
            j = target_type.name.title().replace("_", "")
            self.__dict__[j] = RuleUpdateDeclaration(self, target_type)

    def update(self, full_name, **kwargs):
        DepgRulesFactory.all_updates[full_name] = dict(
            args=kwargs, update_func=None)
        def updatorDecorator(update_func):
            DepgRulesFactory.all_updates[full_name].update_func = update_func
        return updatorDecorator

    def hasUpdate(self, full_name):
        return full_name in DepgRulesFactory.all_updates
