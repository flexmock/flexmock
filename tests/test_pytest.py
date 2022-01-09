"""Test flexmock with pytest."""
# pylint: disable=missing-docstring,redefined-outer-name,no-self-use
import unittest

import pytest

from flexmock import flexmock
from flexmock._api import flexmock_teardown
from flexmock.exceptions import MethodCallError
from tests.features import FlexmockTestCase
from tests.utils import assert_raises


def test_module_level_test_for_pytest():
    flexmock(foo="bar").should_receive("foo").once()
    with assert_raises(
        MethodCallError, "foo() expected to be called exactly 1 time, called 0 times"
    ):
        flexmock_teardown()


@pytest.fixture()
def runtest_hook_fixture():
    return flexmock(foo="bar").should_receive("foo").once().mock()


def test_runtest_hook_with_fixture_for_pytest(runtest_hook_fixture):
    runtest_hook_fixture.foo()


def test_flexmock_teardown_works_with_pytest_part1():
    flexmock().should_receive("method1").ordered()


def test_flexmock_teardown_works_with_pytest_part2():
    mock = flexmock().should_receive("method2").ordered().mock()
    # Raises CallOrderError if flexmock teardown is not automatically called
    # after test part 1 above
    mock.method2()


class TestForPytest(FlexmockTestCase):
    def test_class_level_test_for_pytest(self):
        flexmock(foo="bar").should_receive("foo").once()
        with assert_raises(
            MethodCallError, "foo() expected to be called exactly 1 time, called 0 times"
        ):
            flexmock_teardown()


class TestUnittestClass(unittest.TestCase):
    def test_unittest(self):
        mocked = flexmock(a=2)
        mocked.should_receive("a").once()
        with assert_raises(
            MethodCallError, "a() expected to be called exactly 1 time, called 0 times"
        ):
            flexmock_teardown()


class TestFailureOnException:
    def _setup_failing_expectation(self):
        flexmock(foo="bar").should_receive("foo").once()

    # Use xfail to ensure we process exceptions as returned by _hook_into_pytest

    @pytest.mark.xfail(raises=RuntimeError)
    def test_exception(self):
        raise RuntimeError("TEST ERROR")

    @pytest.mark.xfail(raises=MethodCallError)
    def test_flexmock_raises_if_no_exception(self):
        self._setup_failing_expectation()

    @pytest.mark.xfail(raises=RuntimeError)
    def test_flexmock_doesnt_override_existing_exception(self):
        self._setup_failing_expectation()
        raise RuntimeError("Flexmock shouldn't suppress this exception")

    @pytest.mark.xfail(raises=AssertionError)
    def test_flexmock_doesnt_override_assertion(self):
        self._setup_failing_expectation()
        assert False, "Flexmock shouldn't suppress this assertion"
