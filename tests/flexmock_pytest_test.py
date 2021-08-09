"""Test flexmock with pytest."""
# pylint: disable=missing-docstring,redefined-outer-name,no-self-use
import pytest

from flexmock import MethodCallError, flexmock, flexmock_teardown
from tests import flexmock_test
from tests.flexmock_test import assert_raises


def test_module_level_test_for_pytest():
    flexmock(foo="bar").should_receive("foo").once()
    assert_raises(MethodCallError, flexmock_teardown)


@pytest.fixture()
def runtest_hook_fixture():
    return flexmock(foo="bar").should_receive("foo").once.mock()


def test_runtest_hook_with_fixture_for_pytest(runtest_hook_fixture):
    runtest_hook_fixture.foo()


class TestForPytest(flexmock_test.RegularClass):
    def test_class_level_test_for_pytest(self):
        flexmock(foo="bar").should_receive("foo").once()
        assert_raises(MethodCallError, flexmock_teardown)


class TestUnittestClass(flexmock_test.TestFlexmockUnittest):
    def test_unittest(self):
        mocked = flexmock(a=2)
        mocked.should_receive("a").once()
        assert_raises(MethodCallError, flexmock_teardown)


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
