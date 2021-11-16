"""Test testtools integration."""
# pylint: disable=missing-docstring,no-self-use
from contextlib import suppress

from testtools import TestCase
from testtools.matchers import Equals

from flexmock import exceptions, flexmock
from flexmock._api import flexmock_teardown


class SomeClass:
    def __init__(self):
        self.value = "some_value"

    def method(self):
        return self.value


class TestFlexmock(TestCase):
    def test_mocking_works(self):

        flexmock(SomeClass).should_receive("method").and_return("mocked_value").once()
        self.assertThat(SomeClass().method(), Equals("mocked_value"))
        flexmock_teardown()
        self.assertThat(SomeClass().method(), Equals("some_value"))

    def test_spying_works(self):
        flexmock(SomeClass).should_call("method").and_return("some_value").once()
        self.assertThat(SomeClass().method(), Equals("some_value"))
        flexmock_teardown()
        self.assertThat(SomeClass().method(), Equals("some_value"))

    def test_exception_is_raised(self):
        mocked = flexmock().should_receive("method").and_return(1).twice().mock()
        self.assertThat(mocked.method(), Equals(1))
        with suppress(exceptions.MethodCallError):
            flexmock_teardown()

    def test_flexmock_teardown_works_with_testtools_part1(self):
        flexmock().should_receive("method1").ordered()

    def test_flexmock_teardown_works_with_testtools_part2(self):
        mock = flexmock().should_receive("method2").ordered().mock()
        # Raises CallOrderError if flexmock teardown is not automatically called
        # after test part 1 above
        mock.method2()
