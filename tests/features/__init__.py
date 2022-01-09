"""Tests for flexmock.

Tests under this module should not depend on any test runner.
"""
from .arg_matching import ArgumentMatchingTestCase
from .call_count import CallCountTestCase
from .common import CommonTestCase
from .conditional import ConditionalAssertionsTestCase
from .derived import DerivedTestCase
from .mocking import MockingTestCase
from .ordered import OrderedTestCase
from .proxied import ProxiedTestCase
from .spying import SpyingTestCase
from .stubbing import StubbingTestCase
from .teardown import TeardownTestCase


class FlexmockTestCase(
    ArgumentMatchingTestCase,
    CallCountTestCase,
    CommonTestCase,
    ConditionalAssertionsTestCase,
    DerivedTestCase,
    MockingTestCase,
    OrderedTestCase,
    ProxiedTestCase,
    SpyingTestCase,
    StubbingTestCase,
    TeardownTestCase,
):
    """This class should be imported by other test modules to run full flexmock
    test suite.
    """
