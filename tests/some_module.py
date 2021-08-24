"""Bogus module for testing."""
# pylint: disable=missing-docstring,disallowed-name,invalid-name


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
