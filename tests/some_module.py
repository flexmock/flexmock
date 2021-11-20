"""Bogus module for testing."""
# pylint: disable=missing-docstring,disallowed-name,invalid-name,no-self-use

MODULE_LEVEL_ATTRIBUTE = "test"


class SomeClass:
    CLASS_VALUE = "class_method"

    def __init__(self):
        self.instance_value = "instance_method"

    @classmethod
    def class_method(cls):
        return cls.CLASS_VALUE

    @classmethod
    def class_method_with_args(cls, a):
        return a

    @staticmethod
    def static_method():
        return "static_method"

    @staticmethod
    def static_method_with_args(a):
        return a

    def instance_method(self):
        return self.instance_value

    def instance_method_with_args(self, a):
        return a


class DerivedClass(SomeClass):
    pass


class ModuleClass:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def a(self):
        return self.x + self.y


def module_function(x, y):
    return x - y


def kwargs_only_func1(foo, *, bar, baz=5):
    return foo + bar + baz


def kwargs_only_func2(foo, *, bar, baz):
    return foo + bar + baz
