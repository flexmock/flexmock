"""Flexmock testing library for Python."""
from flexmock.api import flexmock
from flexmock.integrations import hook_into_doctest, hook_into_pytest, hook_into_unittest

__all__ = ["flexmock"]

hook_into_pytest()
hook_into_doctest()
hook_into_unittest()
