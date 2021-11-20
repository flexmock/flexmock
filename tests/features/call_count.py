"""Tests for call count modifiers."""
# pylint: disable=missing-docstring,no-self-use,no-member

from flexmock import exceptions, flexmock
from flexmock._api import flexmock_teardown
from tests.utils import assert_raises


class CallCountTestCase:
    def test_support_at_least_and_at_most_together(self):
        class Foo:
            def method(self):
                pass

        instance = Foo()
        flexmock(instance).should_call("method").at_least().once().at_most().twice()
        with assert_raises(
            exceptions.MethodCallError,
            "method() expected to be called at least 1 time and at most 2 times, called 0 times",
        ):
            flexmock_teardown()

        flexmock(instance).should_call("method").at_least().once().at_most().twice()
        instance.method()
        instance.method()
        with assert_raises(
            exceptions.MethodCallError,
            "method() expected to be called at most 2 times, called 3 times",
        ):
            instance.method()

        flexmock(instance).should_call("method").at_least().once().at_most().twice()
        instance.method()
        flexmock_teardown()

        flexmock(instance).should_call("method").at_least().once().at_most().twice()
        instance.method()
        instance.method()
        flexmock_teardown()

    def test_at_least_cannot_be_used_twice(self):
        class Foo:
            def method(self):
                pass

        expectation = flexmock(Foo).should_receive("method")
        with assert_raises(exceptions.FlexmockError, "cannot use at_least modifier twice"):
            expectation.at_least().at_least()

    def test_at_most_cannot_be_used_twice(self):
        class Foo:
            def method(self):
                pass

        expectation = flexmock(Foo).should_receive("method")
        with assert_raises(exceptions.FlexmockError, "cannot use at_most modifier twice"):
            expectation.at_most().at_most()

    def test_at_least_cannot_be_specified_until_at_most_is_set(self):
        class Foo:
            def method(self):
                pass

        expectation = flexmock(Foo).should_receive("method")
        with assert_raises(exceptions.FlexmockError, "cannot use at_most with at_least unset"):
            expectation.at_least().at_most()

    def test_at_most_cannot_be_specified_until_at_least_is_set(self):
        class Foo:
            def method(self):
                pass

        expectation = flexmock(Foo).should_receive("method")
        with assert_raises(exceptions.FlexmockError, "cannot use at_least with at_most unset"):
            expectation.at_most().at_least()
