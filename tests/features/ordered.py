"""Tests for flexmock ordered feature."""
# pylint: disable=missing-docstring,no-self-use,no-member
import re

from flexmock import exceptions, flexmock
from tests.utils import assert_raises


class OrderedTestCase:
    def test_ordered_on_different_methods(self):
        class String(str):
            pass

        string = String("abc")
        flexmock(string)
        string.should_call("startswith").with_args("asdf", 0, 4).ordered()
        string.should_call("endswith").ordered()
        with assert_raises(
            exceptions.CallOrderError,
            re.compile(
                r'endswith\("c"\) called before startswith'
                # Argument names are displayed in PyPy
                r'\((prefix=)?"asdf", (start=)?0, (end=)?4\)'
            ),
        ):
            string.endswith("c")

    def test_flexmock_ordered_worked_after_default_stub(self):
        mocked = flexmock()
        mocked.should_receive("bar")
        mocked.should_receive("bar").with_args("a").ordered()
        mocked.should_receive("bar").with_args("b").ordered()
        with assert_raises(exceptions.CallOrderError, 'bar("b") called before bar("a")'):
            mocked.bar("b")

    def test_flexmock_ordered_works_with_same_args(self):
        mocked = flexmock()
        mocked.should_receive("bar").ordered().and_return(1)
        mocked.should_receive("bar").ordered().and_return(2)
        assert mocked.bar() == 1
        assert mocked.bar() == 2

    def test_flexmock_ordered_works_with_same_args_after_default_stub(self):
        mocked = flexmock()
        mocked.should_receive("bar").and_return(9)
        mocked.should_receive("bar").ordered().and_return(1)
        mocked.should_receive("bar").ordered().and_return(2)
        assert mocked.bar() == 1
        assert mocked.bar() == 2
        assert mocked.bar() == 9
