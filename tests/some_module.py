"""Bogus module for testing."""
# pylint: disable=missing-docstring,disallowed-name,invalid-name


class SomeClass:  # pylint: disable=too-few-public-methods
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def a(self):
        return self.x + self.y


def foo_function(x, y):
    return x - y


def kwargs_only_func(foo, *, bar, baz=5):
    return foo + bar + baz
