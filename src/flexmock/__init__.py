"""Flexmock testing library for Python."""
from flexmock.api import flexmock
from flexmock.integrations import (
    hook_into_doctest,
    hook_into_pytest,
    hook_into_subunit,
    hook_into_teamcity_unittest,
    hook_into_testtools,
    hook_into_twisted,
    hook_into_unittest,
    hook_into_zope,
)

__all__ = ["flexmock"]

hook_into_doctest()
hook_into_pytest()
hook_into_subunit()
hook_into_teamcity_unittest()
hook_into_testtools()
hook_into_twisted()
hook_into_unittest()
hook_into_zope()
