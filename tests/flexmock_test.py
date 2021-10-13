"""Flexmock tests."""
# pylint: disable=missing-docstring,too-many-lines,disallowed-name,no-member,invalid-name,no-self-use
import functools
import os
import random
import re
import sys
import unittest
from contextlib import contextmanager
from typing import Type, Union

from flexmock._api import (
    AT_LEAST,
    AT_MOST,
    EXACTLY,
    RE_TYPE,
    UPDATED_ATTRS,
    CallOrderError,
    ExceptionClassError,
    ExceptionMessageError,
    FlexmockContainer,
    FlexmockError,
    MethodCallError,
    MethodSignatureError,
    Mock,
    MockBuiltinError,
    ReturnValue,
    StateError,
    _format_args,
    _is_class_method,
    _is_static_method,
    _isproperty,
    flexmock,
    flexmock_teardown,
)
from tests import some_module

from .proxy import Proxy


def module_level_function(some, args):
    return f"{some}, {args}"


MODULE_LEVEL_ATTRIBUTE = "test"


class SomeClass:
    CLASS_VALUE = "class_method"

    def __init__(self):
        self.instance_value = "instance_method"

    @classmethod
    def class_method(cls):
        return cls.CLASS_VALUE

    @classmethod
    def class_method_with_args(cls, a):
        return a

    @staticmethod
    def static_method():
        return "static_method"

    @staticmethod
    def static_method_with_args(a):
        return a

    def instance_method(self):
        return self.instance_value

    def instance_method_with_args(self, a):
        return a


class DerivedClass(SomeClass):
    pass


@contextmanager
def assert_raises(expected_exception: Type[BaseException], match: Union[RE_TYPE, str, None]):
    """Assert that code raises the correct exception with a correct error message.

    Args:
        expected_exception: Type of the expected exception.
        match: String or pattern to match the error message against. Use None
          to skip error message checking.
    """
    try:
        yield
    except Exception as raised_exception:
        if not isinstance(raised_exception, expected_exception):
            raise AssertionError(
                f"Expected exception '{type(expected_exception)}' "
                f"but '{type(raised_exception)}' was raised"
            ) from raised_exception
        if match is not None:
            fail = False
            if isinstance(match, RE_TYPE):
                fail = not match.search(str(raised_exception))
                match = match.pattern
            else:
                fail = str(raised_exception) != str(match)
            if fail:
                raise AssertionError(
                    f"Expected error message:\n{'-'*39}\n'{str(match)}'\n"
                    f"\nBut got:\n\n'{str(raised_exception)}'\n{'-'*39}\n"
                ) from raised_exception
    else:
        raise AssertionError(f"Exception '{expected_exception.__name__}' not raised")


def assert_equal(expected, received, msg=""):
    if not msg:
        msg = f"expected {expected}, received {received}"
    if expected != received:
        raise AssertionError(f"{expected} != {received} : {msg}")


class RegularClass:
    def _tear_down(self):
        return flexmock_teardown()

    def test_print_expectation(self):
        mock = flexmock()
        expectation = mock.should_receive("foo")
        assert str(expectation) == "foo() -> ()"

    def test_flexmock_should_create_mock_object(self):
        mock = flexmock()
        assert isinstance(mock, Mock)

    def test_flexmock_should_create_mock_object_from_dict(self):
        mock = flexmock(foo="foo", bar="bar")
        assert_equal("foo", mock.foo)
        assert_equal("bar", mock.bar)

    def test_flexmock_should_add_expectations(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert "method_foo" in [x._name for x in FlexmockContainer.flexmock_objects[mock]]

    def test_flexmock_should_return_value(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar")
        mock.should_receive("method_bar").and_return("value_baz")
        assert_equal("value_bar", mock.method_foo())
        assert_equal("value_baz", mock.method_bar())

    def test_type_flexmock_with_unicode_string_in_should_receive(self):
        class Foo:
            def bar(self):
                return "bar"

        flexmock(Foo).should_receive("bar").and_return("mocked_bar")

        foo = Foo()
        assert_equal("mocked_bar", foo.bar())

    def test_flexmock_should_accept_shortcuts_for_creating_mock_object(self):
        mock = flexmock(attr1="value 1", attr2=lambda: "returning 2")
        assert_equal("value 1", mock.attr1)
        assert_equal("returning 2", mock.attr2())

    def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
        class Foo:
            def method1(self):
                pass

            def method2(self):
                pass

        foo = Foo()
        flexmock(foo, method1="returning 1", method2="returning 2")
        assert_equal("returning 1", foo.method1())
        assert_equal("returning 2", foo.method2())
        assert_equal("returning 2", foo.method2())

    def test_flexmock_expectations_returns_all(self):
        mock = flexmock(name="temp")
        assert mock not in FlexmockContainer.flexmock_objects
        mock.should_receive("method_foo")
        mock.should_receive("method_bar")
        assert_equal(2, len(FlexmockContainer.flexmock_objects[mock]))

    def test_flexmock_expectations_returns_named_expectation(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert_equal(
            "method_foo",
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._name,
        )

    def test_flexmock_expectations_returns_none_if_not_found(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_bar") is None

    def test_flexmock_should_check_parameters(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("bar").and_return(1)
        mock.should_receive("method_foo").with_args("baz").and_return(2)
        assert_equal(1, mock.method_foo("bar"))
        assert_equal(2, mock.method_foo("baz"))

    def test_flexmock_should_keep_track_of_calls(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("foo").and_return(0)
        mock.should_receive("method_foo").with_args("bar").and_return(1)
        mock.should_receive("method_foo").with_args("baz").and_return(2)
        mock.method_foo("bar")
        mock.method_foo("bar")
        mock.method_foo("baz")
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("foo",))
        assert_equal(0, expectation._times_called)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("bar",))
        assert_equal(2, expectation._times_called)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("baz",))
        assert_equal(1, expectation._times_called)

    def test_flexmock_should_set_expectation_call_numbers(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").times(1)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        with assert_raises(
            MethodCallError, "method_foo() expected to be called exactly 1 time, called 0 times"
        ):
            expectation._verify()
        mock.method_foo()
        expectation._verify()

    def test_flexmock_should_check_raised_exceptions(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            pass

        mock.should_receive("method_foo").and_raise(FakeException)
        with assert_raises(FakeException, ""):
            mock.method_foo()
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called,
        )

    def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException(1, arg2=2))
        with assert_raises(FakeException, "1"):
            mock.method_foo()
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called,
        )

    def test_flexmock_should_check_raised_exceptions_class_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException, 1, arg2=2)
        with assert_raises(FakeException, "1"):
            mock.method_foo()
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called,
        )

    def test_flexmock_should_match_any_args_by_default(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar")
        mock.should_receive("method_foo").with_args("baz").and_return("baz")
        assert_equal("bar", mock.method_foo())
        assert_equal("bar", mock.method_foo(1))
        assert_equal("bar", mock.method_foo("foo", "bar"))
        assert_equal("baz", mock.method_foo("baz"))

    def test_spying_non_existent_mock_object_method_should_fail(self):
        mock = flexmock()
        with assert_raises(
            FlexmockError,
            "Mock object does not have attribute 'method_foo'. "
            'Did you mean to call should_receive("method_foo") instead?',
        ):
            mock.should_call("method_foo")
        mock = flexmock(method_foo=lambda: "ok")
        mock.should_call("method_foo")

    def test_flexmock_should_fail_to_match_exactly_no_args_when_calling_with_args(self):
        mock = flexmock()
        mock.should_receive("method_foo").with_args()
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method_foo did not match expectations:\n"
                '  Received call:\tmethod_foo("baz")\n'
                "  Expected call[1]:\tmethod_foo()"
            ),
        ):
            mock.method_foo("baz")

    def test_flexmock_should_match_exactly_no_args(self):
        class Foo:
            def bar(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("bar").with_args().and_return("baz")
        assert_equal("baz", foo.bar())

    def test_expectation_dot_mock_should_return_mock(self):
        mock = flexmock(name="temp")
        assert_equal(mock, mock.should_receive("method_foo").mock)

    def test_flexmock_should_create_partial_new_style_object_mock(self):
        class User:
            def __init__(self, name=None):
                self.name = name

            def get_name(self):
                return self.name

            def set_name(self, name):
                self.name = name

        user = User()
        flexmock(user)
        user.should_receive("get_name").and_return("john")
        user.set_name("mike")
        assert_equal("john", user.get_name())

    def test_flexmock_should_create_partial_old_style_object_mock(self):
        class User:
            def __init__(self, name=None):
                self.name = name

            def get_name(self):
                return self.name

            def set_name(self, name):
                self.name = name

        user = User()
        flexmock(user)
        user.should_receive("get_name").and_return("john")
        user.set_name("mike")
        assert_equal("john", user.get_name())

    def test_flexmock_should_create_partial_new_style_class_mock(self):
        class User:
            def __init__(self):
                pass

            def get_name(self):
                pass

        flexmock(User)
        User.should_receive("get_name").and_return("mike")
        user = User()
        assert_equal("mike", user.get_name())

    def test_flexmock_should_create_partial_old_style_class_mock(self):
        class User:
            def __init__(self):
                pass

            def get_name(self):
                pass

        flexmock(User)
        User.should_receive("get_name").and_return("mike")
        user = User()
        assert_equal("mike", user.get_name())

    def test_flexmock_should_match_expectations_against_builtin_classes(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args(str).and_return("got a string")
        mock.should_receive("method_foo").with_args(int).and_return("got an int")
        assert_equal("got a string", mock.method_foo("string!"))
        assert_equal("got an int", mock.method_foo(23))
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method_foo did not match expectations:\n"
                "  Received call:\tmethod_foo(2.0)\n"
                "  Expected call[1]:\tmethod_foo(<class 'int'>)\n"
                "  Expected call[2]:\tmethod_foo(<class 'str'>)"
            ),
        ):
            mock.method_foo(2.0)

    def test_with_args_should_work_with_builtin_c_methods(self):
        flexmock(sys.stdout).should_call("write")  # set fall-through
        flexmock(sys.stdout).should_receive("write").with_args("flexmock_builtin_test")
        sys.stdout.write("flexmock_builtin_test")

    def test_with_args_should_work_with_builtin_c_functions(self):
        mocked = flexmock(sys)
        mocked.should_receive("exit").with_args(1).once()
        mocked.exit(1)
        self._tear_down()
        flexmock(os).should_receive("remove").with_args("path").once()
        os.remove("path")

    def test_with_args_should_work_with_builtin_python_methods(self):
        flexmock(random).should_receive("randint").with_args(1, 10).once()
        random.randint(1, 10)

    def test_flexmock_should_match_expectations_against_user_defined_classes(self):
        mock = flexmock(name="temp")

        class Foo:
            pass

        mock.should_receive("method_foo").with_args(Foo).and_return("got a Foo")
        assert_equal("got a Foo", mock.method_foo(Foo()))
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method_foo did not match expectations:\n"
                "  Received call:\tmethod_foo(1)\n"
                "  Expected call[1]:\tmethod_foo(<class 'tests.flexmock_test.RegularClass.test"
                "_flexmock_should_match_expectations_against_user_defined_classes.<locals>.Foo'>)"
            ),
        ):
            mock.method_foo(1)

    def test_flexmock_configures_global_mocks_dict(self):
        mock = flexmock(name="temp")
        assert mock not in FlexmockContainer.flexmock_objects
        mock.should_receive("method_foo")
        assert mock in FlexmockContainer.flexmock_objects
        assert_equal(len(FlexmockContainer.flexmock_objects[mock]), 1)

    def test_flexmock_teardown_verifies_mocks(self):
        mock = flexmock(name="temp")
        mock.should_receive("verify_expectations").times(1)
        with assert_raises(
            MethodCallError,
            "verify_expectations() expected to be called exactly 1 time, called 0 times",
        ):
            self._tear_down()

    def test_flexmock_teardown_does_not_verify_stubs(self):
        mock = flexmock(name="temp")
        mock.should_receive("verify_expectations")
        self._tear_down()

    def test_flexmock_preserves_stubbed_object_methods_between_tests(self):
        class User:
            def get_name(self):
                return "mike"

        user = User()
        flexmock(user).should_receive("get_name").and_return("john")
        assert_equal("john", user.get_name())
        self._tear_down()
        assert_equal("mike", user.get_name())

    def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
        class User:
            def get_name(self):
                return "mike"

        user = User()
        flexmock(User).should_receive("get_name").and_return("john")
        assert_equal("john", user.get_name())
        self._tear_down()
        assert_equal("mike", user.get_name())

    def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
        class User:
            def get_name(self):
                pass

        user = User()
        saved = user.get_name
        flexmock(user).should_receive("get_name").and_return("john")
        assert saved != user.get_name
        assert_equal("john", user.get_name())
        self._tear_down()
        assert_equal(saved, user.get_name)

    def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
        class User:
            def get_name(self):
                pass

        user = User()
        saved = user.get_name
        flexmock(User).should_receive("get_name").and_return("john")
        assert saved != user.get_name
        assert_equal("john", user.get_name())
        self._tear_down()
        assert_equal(saved, user.get_name)

    def test_flexmock_removes_stubs_from_multiple_objects_on_teardown(self):
        class User:
            def get_name(self):
                pass

        class Group:
            def get_name(self):
                pass

        user = User()
        group = Group()
        saved1 = user.get_name
        saved2 = group.get_name
        flexmock(user).should_receive("get_name").and_return("john").once()
        flexmock(group).should_receive("get_name").and_return("john").once()
        assert saved1 != user.get_name
        assert saved2 != group.get_name
        assert_equal("john", user.get_name())
        assert_equal("john", group.get_name())
        self._tear_down()
        assert_equal(saved1, user.get_name)
        assert_equal(saved2, group.get_name)

    def test_flexmock_removes_stubs_from_multiple_classes_on_teardown(self):
        class User:
            def get_name(self):
                pass

        class Group:
            def get_name(self):
                pass

        user = User()
        group = User()
        saved1 = user.get_name
        saved2 = group.get_name
        flexmock(User).should_receive("get_name").and_return("john")
        flexmock(Group).should_receive("get_name").and_return("john")
        assert saved1 != user.get_name
        assert saved2 != group.get_name
        assert_equal("john", user.get_name())
        assert_equal("john", group.get_name())
        self._tear_down()
        assert_equal(saved1, user.get_name)
        assert_equal(saved2, group.get_name)

    def test_flexmock_respects_at_least_when_called_less_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar").at_least().twice()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_LEAST, expectation._modifier)
        mock.method_foo()
        with assert_raises(
            MethodCallError, "method_foo() expected to be called at least 2 times, called 1 time"
        ):
            self._tear_down()

    def test_flexmock_respects_at_least_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_LEAST, expectation._modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_least_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_LEAST, expectation._modifier)
        mock.method_foo()
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_less_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar").at_most().twice()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation._modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation._modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation._modifier)
        mock.method_foo()
        with assert_raises(
            MethodCallError, "method_foo() expected to be called at most 1 time, called 2 times"
        ):
            mock.method_foo()

    def test_flexmock_treats_once_as_times_one(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(1, expectation._expected_calls[EXACTLY])
        with assert_raises(
            MethodCallError, "method_foo() expected to be called exactly 1 time, called 0 times"
        ):
            self._tear_down()

    def test_flexmock_treats_twice_as_times_two(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").twice().and_return("value_bar")
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(2, expectation._expected_calls[EXACTLY])
        with assert_raises(
            MethodCallError, "method_foo() expected to be called exactly 2 times, called 0 times"
        ):
            self._tear_down()

    def test_flexmock_works_with_never_when_true(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(0, expectation._expected_calls[EXACTLY])
        self._tear_down()

    def test_flexmock_works_with_never_when_false(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        with assert_raises(
            MethodCallError, "method_foo() expected to be called exactly 0 times, called 1 time"
        ):
            mock.method_foo()

    def test_flexmock_get_flexmock_expectation_should_work_with_args(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("value_bar")
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo", "value_bar")

    def test_flexmock_function_should_return_previously_mocked_object(self):
        class User:
            pass

        user = User()
        foo = flexmock(user)
        assert foo == user
        assert foo == flexmock(user)

    def test_flexmock_should_not_return_class_object_if_mocking_instance(self):
        class User:
            def method(self):
                pass

        user = User()
        user2 = User()
        class_mock = flexmock(User).should_receive("method").and_return("class").mock
        user_mock = flexmock(user).should_receive("method").and_return("instance").mock
        assert class_mock is not user_mock
        assert_equal("instance", user.method())
        assert_equal("class", user2.method())

    def test_should_call_with_class_default_attributes(self):
        """Flexmock should not allow mocking class default attributes like
        __call__ on an instance.
        """

        class WithCall:
            def __call__(self, a):
                return a

        instance = WithCall()

        with assert_raises(
            FlexmockError,
            re.compile(r".+<locals>\.WithCall object at 0x.+> does not have attribute '__call__'"),
        ):
            flexmock(instance).should_call("__call__")

    def test_should_call_on_class_mock(self):
        class User:
            def __init__(self):
                self.value = "value"

            def foo(self):
                return "class"

            def bar(self):
                return self.value

        # Access class-level method
        user1 = User()
        user2 = User()
        flexmock(User).should_call("foo").once()
        with assert_raises(
            MethodCallError, "foo() expected to be called exactly 1 time, called 0 times"
        ):
            self._tear_down()
        flexmock(User).should_call("foo").twice()
        assert_equal("class", user1.foo())
        assert_equal("class", user2.foo())

        # Access instance attributes
        flexmock(User).should_call("bar").once()
        with assert_raises(
            MethodCallError, "bar() expected to be called exactly 1 time, called 0 times"
        ):
            self._tear_down()
        flexmock(User).should_call("bar").twice()
        assert_equal("value", user1.bar())
        assert_equal("value", user2.bar())

        # Try resetting the expectation
        flexmock(User).should_call("bar").once()
        assert_equal("value", user1.bar())

    def test_mock_proxied_class(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        flexmock(SomeClassProxy).should_receive("class_method").and_return(2).twice()
        assert SomeClassProxy().class_method() == 2
        assert SomeClassProxy.class_method() == 2
        flexmock(SomeClassProxy).should_receive("static_method").and_return(3).twice()
        assert SomeClassProxy().static_method() == 3
        assert SomeClassProxy.static_method() == 3
        instance = SomeClassProxy()
        flexmock(instance).should_receive("instance_method").and_return(4).once()
        assert instance.instance_method() == 4

    def test_mock_proxied_class_with_args(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        flexmock(SomeClassProxy).should_receive("class_method_with_args").with_args("a").and_return(
            2
        ).twice()
        assert SomeClassProxy().class_method_with_args("a") == 2
        assert SomeClassProxy.class_method_with_args("a") == 2
        flexmock(SomeClassProxy).should_receive("static_method_with_args").with_args(
            "b"
        ).and_return(3).twice()
        assert SomeClassProxy().static_method_with_args("b") == 3
        assert SomeClassProxy.static_method_with_args("b") == 3
        instance = SomeClassProxy()
        flexmock(instance).should_receive("instance_method_with_args").with_args("c").and_return(
            4
        ).once()
        assert instance.instance_method_with_args("c") == 4

    def test_spy_proxied_class(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        flexmock(SomeClassProxy).should_call("class_method").and_return("class_method").twice()
        assert SomeClassProxy().class_method() == "class_method"
        assert SomeClassProxy.class_method() == "class_method"
        flexmock(SomeClassProxy).should_call("static_method").and_return("static_method").twice()
        assert SomeClassProxy().static_method() == "static_method"
        assert SomeClassProxy.static_method() == "static_method"
        instance = SomeClassProxy()
        flexmock(instance).should_call("instance_method").and_return("instance_method").once()
        assert instance.instance_method() == "instance_method"

    def test_spy_proxied_class_with_args(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        flexmock(SomeClassProxy).should_call("class_method_with_args").with_args("a").and_return(
            "a"
        ).twice()
        assert SomeClassProxy().class_method_with_args("a") == "a"
        assert SomeClassProxy.class_method_with_args("a") == "a"
        flexmock(SomeClassProxy).should_call("static_method_with_args").with_args("b").and_return(
            "b"
        ).twice()
        assert SomeClassProxy().static_method_with_args("b") == "b"
        assert SomeClassProxy.static_method_with_args("b") == "b"
        instance = SomeClassProxy()
        flexmock(instance).should_call("instance_method_with_args").with_args("c").and_return(
            "c"
        ).once()
        assert instance.instance_method_with_args("c") == "c"

    def test_mock_proxied_derived_class(self):
        # pylint: disable=not-callable
        DerivedClassProxy = Proxy(DerivedClass)
        flexmock(DerivedClassProxy).should_receive("class_method").and_return(2).twice()
        assert DerivedClassProxy().class_method() == 2
        assert DerivedClassProxy.class_method() == 2
        flexmock(DerivedClassProxy).should_receive("static_method").and_return(3).twice()
        assert DerivedClassProxy().static_method() == 3
        assert DerivedClassProxy.static_method() == 3
        instance = DerivedClassProxy()
        flexmock(instance).should_receive("instance_method").and_return(4).once()
        assert instance.instance_method() == 4

    def test_mock_proxied_module_function(self):
        # pylint: disable=not-callable
        some_module_proxy = Proxy(some_module)
        flexmock(some_module_proxy).should_receive("module_function").and_return(3).once()
        assert some_module_proxy.module_function() == 3

    def test_spy_proxied_module_function(self):
        # pylint: disable=not-callable
        some_module_proxy = Proxy(some_module)
        flexmock(some_module_proxy).should_receive("module_function").and_return(0).once()
        assert some_module_proxy.module_function(2, 2) == 0

    def test_mock_proxied_derived_class_with_args(self):
        # pylint: disable=not-callable
        DerivedClassProxy = Proxy(DerivedClass)
        flexmock(DerivedClassProxy).should_receive("class_method_with_args").with_args(
            "a"
        ).and_return(2).twice()
        assert DerivedClassProxy().class_method_with_args("a") == 2
        assert DerivedClassProxy.class_method_with_args("a") == 2
        flexmock(DerivedClassProxy).should_receive("static_method_with_args").with_args(
            "b"
        ).and_return(3).twice()
        assert DerivedClassProxy().static_method_with_args("b") == 3
        assert DerivedClassProxy.static_method_with_args("b") == 3
        instance = DerivedClassProxy()
        flexmock(instance).should_receive("instance_method_with_args").with_args("c").and_return(
            4
        ).once()
        assert instance.instance_method_with_args("c") == 4

    def test_spy_proxied_derived_class(self):
        # pylint: disable=not-callable
        DerivedClassProxy = Proxy(DerivedClass)
        flexmock(DerivedClassProxy).should_call("class_method").and_return("class_method").twice()
        assert DerivedClassProxy().class_method() == "class_method"
        assert DerivedClassProxy.class_method() == "class_method"
        flexmock(DerivedClassProxy).should_call("static_method").and_return("static_method").twice()
        assert DerivedClassProxy().static_method() == "static_method"
        assert DerivedClassProxy.static_method() == "static_method"
        instance = DerivedClassProxy()
        flexmock(instance).should_call("instance_method").and_return("instance_method").once()
        assert instance.instance_method() == "instance_method"

    def test_spy_proxied_derived_class_with_args(self):
        # pylint: disable=not-callable
        DerivedClassProxy = Proxy(DerivedClass)
        flexmock(DerivedClassProxy).should_call("class_method_with_args").with_args("a").and_return(
            "a"
        ).twice()
        assert DerivedClassProxy().class_method_with_args("a") == "a"
        assert DerivedClassProxy.class_method_with_args("a") == "a"
        flexmock(DerivedClassProxy).should_call("static_method_with_args").with_args(
            "b"
        ).and_return("b").twice()
        assert DerivedClassProxy().static_method_with_args("b") == "b"
        assert DerivedClassProxy.static_method_with_args("b") == "b"
        instance = DerivedClassProxy()
        flexmock(instance).should_call("instance_method_with_args").with_args("c").and_return(
            "c"
        ).once()
        assert instance.instance_method_with_args("c") == "c"

    def test_with_args_with_instance_method(self):
        flexmock(SomeClass).should_receive("instance_method_with_args").with_args("red").once()
        flexmock(SomeClass).should_receive("instance_method_with_args").with_args("blue").once()
        instance = SomeClass()
        instance.instance_method_with_args("red")
        instance.instance_method_with_args("blue")

    def test_with_args_with_class_method(self):
        flexmock(SomeClass).should_receive("class_method_with_args").with_args("red").once()
        flexmock(SomeClass).should_receive("class_method_with_args").with_args("blue").once()
        SomeClass.class_method_with_args("red")
        SomeClass.class_method_with_args("blue")

    def test_with_args_with_static_method(self):
        flexmock(SomeClass).should_receive("static_method_with_args").with_args("red").once()
        flexmock(SomeClass).should_receive("static_method_with_args").with_args("blue").once()
        SomeClass.static_method_with_args("red")
        SomeClass.static_method_with_args("blue")

    def test_mock_class_method_on_derived_class(self):
        flexmock(DerivedClass).should_receive("class_method").and_return(2).twice()
        assert DerivedClass().class_method() == 2
        assert DerivedClass.class_method() == 2

    def test_mock_class_method_on_derived_class_after_mocking_base_class(self):
        flexmock(SomeClass).should_receive("class_method").and_return(1).once()
        assert SomeClass.class_method() == 1
        flexmock(DerivedClass).should_receive("class_method").and_return(2).twice()
        assert DerivedClass().class_method() == 2
        assert DerivedClass.class_method() == 2

    def test_mock_static_method_on_derived_class(self):
        flexmock(DerivedClass).should_receive("static_method").and_return(4).twice()
        assert DerivedClass().static_method() == 4
        assert DerivedClass.static_method() == 4

    def test_mock_static_method_on_derived_class_after_mocking_base_class(self):
        flexmock(SomeClass).should_receive("static_method").and_return(3).once()
        assert SomeClass.static_method() == 3
        flexmock(DerivedClass).should_receive("static_method").and_return(4).twice()
        assert DerivedClass().static_method() == 4
        assert DerivedClass.static_method() == 4

    def test_mock_class_method_with_args_on_derived_class(self):
        flexmock(DerivedClass).should_receive("class_method_with_args").with_args(2).and_return(
            3
        ).twice()
        assert DerivedClass().class_method_with_args(2) == 3
        assert DerivedClass.class_method_with_args(2) == 3

    def test_mock_class_method_with_args_on_derived_class_after_mocking_base_class(self):
        flexmock(SomeClass).should_receive("class_method_with_args").with_args(1).and_return(
            2
        ).once()
        assert SomeClass.class_method_with_args(1) == 2
        flexmock(DerivedClass).should_receive("class_method_with_args").with_args(2).and_return(
            3
        ).twice()
        assert DerivedClass().class_method_with_args(2) == 3
        assert DerivedClass.class_method_with_args(2) == 3

    def test_mock_static_method_with_args_on_derived_class(self):
        flexmock(DerivedClass).should_receive("static_method_with_args").with_args(4).and_return(
            5
        ).twice()
        assert DerivedClass().static_method_with_args(4) == 5
        assert DerivedClass.static_method_with_args(4) == 5

    def test_mock_static_method_with_args_on_derived_class_after_mocking_base_class(self):
        flexmock(SomeClass).should_receive("static_method_with_args").with_args(2).and_return(
            3
        ).once()
        assert SomeClass.static_method_with_args(2) == 3
        flexmock(DerivedClass).should_receive("static_method_with_args").with_args(4).and_return(
            5
        ).twice()
        assert DerivedClass().static_method_with_args(4) == 5
        assert DerivedClass.static_method_with_args(4) == 5

    def test_spy_class_method_on_derived_class(self):
        flexmock(DerivedClass).should_call("class_method").and_return("class_method").twice()
        assert DerivedClass().class_method() == "class_method"
        assert DerivedClass.class_method() == "class_method"

    def test_spy_class_method_on_derived_class_after_spying_base_class(self):
        flexmock(SomeClass).should_call("class_method").and_return("class_method").times(
            3
        )  # TODO: Should be once #80
        assert SomeClass.class_method() == "class_method"
        flexmock(DerivedClass).should_call("class_method").and_return("class_method").twice()
        assert DerivedClass().class_method() == "class_method"
        assert DerivedClass.class_method() == "class_method"

    def test_spy_static_method_on_derived_class(self):
        flexmock(DerivedClass).should_call("static_method").and_return("static_method").twice()
        assert DerivedClass().static_method() == "static_method"
        assert DerivedClass.static_method() == "static_method"

    def test_spy_static_method_on_derived_class_after_spying_base_class(self):
        flexmock(SomeClass).should_call("static_method").and_return("static_method").times(
            3
        )  # TODO: Should be once #80
        assert SomeClass.static_method() == "static_method"
        flexmock(DerivedClass).should_call("static_method").and_return("static_method").twice()
        assert DerivedClass().static_method() == "static_method"
        assert DerivedClass.static_method() == "static_method"

    def test_spy_class_method_with_args_on_derived_class(self):
        flexmock(DerivedClass).should_call("class_method_with_args").with_args(2).and_return(2)
        assert DerivedClass().class_method_with_args(2) == 2
        assert DerivedClass.class_method_with_args(2) == 2

    @assert_raises(MethodSignatureError, match=None)  # TODO: Should not raise exception #79
    def test_spy_class_method_with_args_on_derived_class_after_spying_base_class(self):
        flexmock(SomeClass).should_call("class_method_with_args").with_args(1).and_return(1)
        assert SomeClass.class_method_with_args(1) == 1
        flexmock(DerivedClass).should_call("class_method_with_args").with_args(2).and_return(2)
        assert DerivedClass().class_method_with_args(2) == 2
        assert DerivedClass.class_method_with_args(2) == 2

    def test_spy_static_method_with_args_on_derived_class(self):
        flexmock(DerivedClass).should_call("static_method_with_args").with_args(4).and_return(
            4
        ).twice()
        assert DerivedClass().static_method_with_args(4) == 4
        assert DerivedClass.static_method_with_args(4) == 4

    @assert_raises(MethodSignatureError, match=None)  # TODO: Should not raise exception #79
    def test_spy_static_method_with_args_on_derived_class_after_spying_base_class(self):
        flexmock(SomeClass).should_call("static_method_with_args").with_args(2).and_return(2).once()
        assert SomeClass.static_method_with_args(2) == 2
        flexmock(DerivedClass).should_call("static_method_with_args").with_args(4).and_return(
            4
        ).once()  # should be twice
        assert DerivedClass().static_method_with_args(4) == 4
        assert DerivedClass.static_method_with_args(4) == 4

    def test_flexmock_should_not_blow_up_on_should_call_for_class_methods(self):
        class User:
            @classmethod
            def foo(cls):
                return "class"

        flexmock(User).should_call("foo")
        assert_equal("class", User.foo())

    def test_flexmock_should_not_blow_up_on_should_call_for_static_methods(self):
        class User:
            @staticmethod
            def foo():
                return "static"

        flexmock(User).should_call("foo")
        assert_equal("static", User.foo())

    def test_flexmock_should_mock_new_instances_with_multiple_params(self):
        class User:
            pass

        class Group:
            def __init__(self, arg, arg2):
                pass

        user = User()
        flexmock(Group).new_instances(user)
        assert user is Group(1, 2)

    def test_flexmock_should_revert_new_instances_on_teardown(self):
        class User:
            pass

        class Group:
            pass

        user = User()
        group = Group()
        flexmock(Group).new_instances(user)
        assert user is Group()
        self._tear_down()
        assert_equal(group.__class__, Group().__class__)

    def test_flexmock_should_cleanup_added_methods_and_attributes(self):
        class Group:
            pass

        group = Group()
        flexmock(Group)
        assert "should_receive" in Group.__dict__
        assert "should_receive" not in group.__dict__
        flexmock(group)
        assert "should_receive" in group.__dict__
        self._tear_down()
        for method in UPDATED_ATTRS:
            assert method not in Group.__dict__
            assert method not in group.__dict__

    def test_class_attributes_are_unchanged_after_mocking(self):
        class Base:
            @classmethod
            def class_method(cls):
                pass

            @staticmethod
            def static_method():
                pass

            def instance_method(self):
                pass

        class Child(Base):
            pass

        instance = Base()
        base_attrs = list(vars(Base).keys())
        instance_attrs = list(vars(instance).keys())
        child_attrs = list(vars(Child).keys())
        flexmock(Base).should_receive("class_method").once()
        flexmock(Base).should_receive("static_method").once()
        Base.class_method()
        Base.static_method()

        flexmock(instance).should_receive("class_method").once()
        flexmock(instance).should_receive("static_method").once()
        flexmock(instance).should_receive("instance_method").once()
        instance.class_method()
        instance.static_method()
        instance.instance_method()

        flexmock(Child).should_receive("class_method").once()
        flexmock(Child).should_receive("static_method").once()
        Child.class_method()
        Child.static_method()

        self._tear_down()
        assert base_attrs == list(vars(Base).keys())
        assert instance_attrs == list(vars(instance).keys())
        assert child_attrs == list(vars(Child).keys())

    def test_class_attributes_are_unchanged_after_spying(self):
        class Base:
            @classmethod
            def class_method(cls):
                pass

            @staticmethod
            def static_method():
                pass

            def instance_method(self):
                pass

        class Child(Base):
            pass

        instance = Base()
        base_attrs = list(vars(Base).keys())
        instance_attrs = list(vars(instance).keys())
        child_attrs = list(vars(Child).keys())
        flexmock(Base).should_call("class_method").times(3)  # TODO: should be once #80
        flexmock(Base).should_call("static_method").times(3)  # TODO: should be once #80
        Base.class_method()
        Base.static_method()

        flexmock(instance).should_call("class_method").once()
        flexmock(instance).should_call("static_method").once()
        flexmock(instance).should_call("instance_method").once()
        instance.class_method()
        instance.static_method()
        instance.instance_method()

        flexmock(Child).should_call("class_method").once()
        flexmock(Child).should_call("static_method").once()
        Child.class_method()
        Child.static_method()

        self._tear_down()
        assert base_attrs == list(vars(Base).keys())
        assert instance_attrs == list(vars(instance).keys())
        assert child_attrs == list(vars(Child).keys())

    def test_flexmock_should_cleanup_after_exception(self):
        class User:
            def method2(self):
                pass

        class Group:
            def method1(self):
                pass

        flexmock(Group)
        flexmock(User)
        Group.should_receive("method1").once()
        User.should_receive("method2").once()
        with assert_raises(
            MethodCallError, "method1() expected to be called exactly 1 time, called 0 times"
        ):
            self._tear_down()
        for method in UPDATED_ATTRS:
            assert method not in dir(Group)
        for method in UPDATED_ATTRS:
            assert method not in dir(User)

    def test_flexmock_should_call_respects_matched_expectations(self):
        class Group:
            def method1(self, arg1, arg2="b"):
                return f"{arg1}:{arg2}"

            def method2(self, arg):
                return arg

        group = Group()
        flexmock(group).should_call("method1").twice()
        assert_equal("a:c", group.method1("a", arg2="c"))
        assert_equal("a:b", group.method1("a"))
        group.should_call("method2").once().with_args("c")
        assert_equal("c", group.method2("c"))
        self._tear_down()

    def test_flexmock_should_call_respects_unmatched_expectations(self):
        class Group:
            def method1(self, arg1, arg2="b"):
                return f"{arg1}:{arg2}"

            def method2(self, a):
                pass

        group = Group()
        flexmock(group).should_call("method1").at_least().once()
        with assert_raises(
            MethodCallError, "method1() expected to be called at least 1 time, called 0 times"
        ):
            self._tear_down()
        flexmock(group)
        group.should_call("method2").with_args("a").once()
        group.should_receive("method2").with_args("not a")
        group.method2("not a")
        with assert_raises(
            MethodCallError, 'method2(a="a") expected to be called exactly 1 time, called 0 times'
        ):
            self._tear_down()

    def test_flexmock_doesnt_error_on_properly_ordered_expectations(self):
        class Foo:
            def foo(self):
                pass

            def method1(self, a):
                pass

            def bar(self):
                pass

            def baz(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("foo")
        flexmock(foo).should_receive("method1").with_args("a").ordered()
        flexmock(foo).should_receive("bar")
        flexmock(foo).should_receive("method1").with_args("b").ordered()
        flexmock(foo).should_receive("baz")
        foo.bar()
        foo.method1("a")
        foo.method1("b")
        foo.baz()
        foo.foo()

    def test_flexmock_errors_on_improperly_ordered_expectations(self):
        class Foo:
            def method1(self, a):
                pass

        foo = Foo()
        flexmock(foo)
        foo.should_receive("method1").with_args("a").ordered()
        foo.should_receive("method1").with_args("b").ordered()
        with assert_raises(CallOrderError, 'method1("b") called before method1(a="a")'):
            foo.method1("b")

    def test_flexmock_should_accept_multiple_return_values(self):
        class Foo:
            def method1(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").and_return(1, 5).and_return(2)
        assert_equal((1, 5), foo.method1())
        assert_equal(2, foo.method1())
        assert_equal((1, 5), foo.method1())
        assert_equal(2, foo.method1())

    def test_flexmock_should_accept_multiple_return_values_with_shortcut(self):
        class Foo:
            def method1(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").and_return(1, 2).one_by_one()
        assert_equal(1, foo.method1())
        assert_equal(2, foo.method1())
        assert_equal(1, foo.method1())
        assert_equal(2, foo.method1())

    def test_flexmock_should_accept_multiple_return_values_with_one_by_one(self):
        mocked = flexmock()
        flexmock(mocked).should_receive("method1").and_return(2).and_return(3).one_by_one()
        assert_equal(2, mocked.method1())
        assert_equal(3, mocked.method1())
        assert_equal(2, mocked.method1())
        assert_equal(3, mocked.method1())

    def test_one_by_one_called_before_and_return_multiple_values(self):
        mocked = flexmock()
        mocked.should_receive("method1").one_by_one().and_return(3, 4)
        assert_equal(3, mocked.method1())
        assert_equal(4, mocked.method1())
        assert_equal(3, mocked.method1())
        assert_equal(4, mocked.method1())

    def test_one_by_one_called_before_and_return_one_value(self):
        mocked = flexmock()
        mocked.should_receive("method1").one_by_one().and_return(4).and_return(5)
        assert_equal(4, mocked.method1())
        assert_equal(5, mocked.method1())
        assert_equal(4, mocked.method1())
        assert_equal(5, mocked.method1())

    def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
        class Foo:
            def method1(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").and_return(1).and_raise(Exception)
        assert_equal(1, foo.method1())
        with assert_raises(Exception, ""):
            foo.method1()
        assert_equal(1, foo.method1())
        with assert_raises(Exception, ""):
            foo.method1()

    def test_flexmock_should_match_types_on_multiple_arguments(self):
        class Foo:
            def method1(self, a, b):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        assert_equal("ok", foo.method1("some string", 12))
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                "  Received call:\tmethod1(12, 32)\n"
                "  Expected call[1]:\tmethod1(a=<class 'str'>, b=<class 'int'>)"
            ),
        ):
            foo.method1(12, 32)
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                '  Received call:\tmethod1(12, "some string")\n'
                "  Expected call[1]:\tmethod1(a=<class 'str'>, b=<class 'int'>)\n"
                "  Expected call[2]:\tmethod1(a=<class 'str'>, b=<class 'int'>)"
            ),
        ):
            foo.method1(12, "some string")
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                '  Received call:\tmethod1("string", 12, 14)\n'
                "  Expected call[1]:\tmethod1(a=<class 'str'>, b=<class 'int'>)\n"
                "  Expected call[2]:\tmethod1(a=<class 'str'>, b=<class 'int'>)\n"
                "  Expected call[3]:\tmethod1(a=<class 'str'>, b=<class 'int'>)"
            ),
        ):
            foo.method1("string", 12, 14)

    def test_flexmock_should_match_types_on_multiple_arguments_generic(self):
        class Foo:
            def method1(self, a, b, c):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").with_args(object, object, object).and_return("ok")
        assert_equal("ok", foo.method1("some string", None, 12))
        assert_equal("ok", foo.method1((1,), None, 12))
        assert_equal("ok", foo.method1(12, 14, []))
        assert_equal("ok", foo.method1("some string", "another one", False))
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                '  Received call:\tmethod1("string", 12)\n'
                "  Expected call[1]:\tmethod1(a=<class 'object'>, "
                "b=<class 'object'>, c=<class 'object'>)"
            ),
        ):
            foo.method1("string", 12)  # pylint: disable=no-value-for-parameter
        self._tear_down()
        flexmock(foo).should_receive("method1").with_args(object, object, object).and_return("ok")
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                '  Received call:\tmethod1("string", 12, 13, 14)\n'
                "  Expected call[1]:\tmethod1(a=<class 'object'>, "
                "b=<class 'object'>, c=<class 'object'>)"
            ),
        ):
            foo.method1("string", 12, 13, 14)

    def test_flexmock_should_match_types_on_multiple_arguments_classes(self):
        class Foo:
            def method1(self, a, b):
                pass

        class Bar:
            pass

        foo = Foo()
        bar = Bar()
        flexmock(foo).should_receive("method1").with_args(object, Bar).and_return("ok")
        assert_equal("ok", foo.method1("some string", bar))
        with assert_raises(
            MethodSignatureError,
            re.compile(
                "Arguments for call method1 did not match expectations:\n"
                r'  Received call:\tmethod1\(.+\.<locals>\.Bar object at 0x.+>, "some string"\)\n'
                r"  Expected call\[1\]:\tmethod1\(a=<class 'object'>, b=<class.+\.<locals>\.Bar'>\)"
            ),
        ):
            foo.method1(bar, "some string")
        self._tear_down()
        flexmock(foo).should_receive("method1").with_args(object, Bar).and_return("ok")
        with assert_raises(
            MethodSignatureError,
            re.compile(
                "Arguments for call method1 did not match expectations:\n"
                r'  Received call:\tmethod1\(12, "some string"\)\n'
                r"  Expected call\[1\]:\tmethod1\(a=<class 'object'>, b=<class.+\.<locals>\.Bar'>\)"
            ),
        ):
            foo.method1(12, "some string")

    def test_flexmock_should_match_keyword_arguments(self):
        class Foo:
            def method1(self, a, **kwargs):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2).twice()
        foo.method1(1, arg2=2, arg3=3)
        foo.method1(1, arg3=3, arg2=2)
        self._tear_down()
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                "  Received call:\tmethod1(arg2=2, arg3=3)\n"
                "  Expected call[1]:\tmethod1(arg3=3, arg2=2, a=1)"
            ),
        ):
            foo.method1(arg2=2, arg3=3)  # pylint: disable=no-value-for-parameter
        self._tear_down()
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                "  Received call:\tmethod1(1, arg2=2, arg3=4)\n"
                "  Expected call[1]:\tmethod1(arg3=3, arg2=2, a=1)"
            ),
        ):
            foo.method1(1, arg2=2, arg3=4)
        self._tear_down()
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call method1 did not match expectations:\n"
                "  Received call:\tmethod1(1)\n"
                "  Expected call[1]:\tmethod1(arg3=3, arg2=2, a=1)"
            ),
        ):
            foo.method1(1)

    def test_flexmock_should_call_should_match_keyword_arguments(self):
        class Foo:
            def method1(self, arg1, arg2=None, arg3=None):
                return f"{arg1}{arg2}{arg3}"

        foo = Foo()
        flexmock(foo).should_call("method1").with_args(1, arg3=3, arg2=2).once()
        assert_equal("123", foo.method1(1, arg2=2, arg3=3))

    def test_flexmock_should_mock_private_methods(self):
        class Foo:
            def __private_method(self):
                return "foo"

            def public_method(self):
                return self.__private_method()

        foo = Foo()
        flexmock(foo).should_receive("__private_method").and_return("bar")
        assert_equal("bar", foo.public_method())

    def test_flexmock_should_mock_special_methods(self):
        class Foo:
            def __special_method__(self):
                return "foo"

            def public_method(self):
                return self.__special_method__()

        foo = Foo()
        flexmock(foo).should_receive("__special_method__").and_return("bar")
        assert_equal("bar", foo.public_method())

    def test_flexmock_should_mock_double_underscore_method(self):
        class Foo:
            def __(self):
                return "foo"

            def public_method(self):
                return self.__()

        foo = Foo()
        flexmock(foo).should_receive("__").and_return("bar")
        assert_equal("bar", foo.public_method())

    def test_flexmock_should_mock_private_class_methods(self):
        class Foo:
            def __iter__(self):
                pass

        flexmock(Foo).should_receive("__iter__").and_yield(1, 2, 3)
        assert_equal([1, 2, 3], list(Foo()))

    def test_flexmock_should_yield_self_when_iterated(self):
        class ClassNoIter:
            pass

        foo = flexmock(ClassNoIter)
        assert foo is list(foo)[0]

    def test_flexmock_should_mock_iter_on_new_style_instances(self):
        class Foo:
            def __iter__(self):
                yield None

        old = Foo.__iter__
        foo = Foo()
        foo2 = Foo()
        foo3 = Foo()
        flexmock(foo, __iter__=iter([1, 2, 3]))
        flexmock(foo2, __iter__=iter([3, 4, 5]))
        assert_equal([1, 2, 3], list(foo))
        assert_equal([3, 4, 5], list(foo2))
        assert_equal([None], list(foo3))
        assert_equal(False, foo.__iter__ is old)
        assert_equal(False, foo2.__iter__ is old)
        assert_equal(False, foo3.__iter__ is old)
        self._tear_down()
        assert_equal([None], list(foo))
        assert_equal([None], list(foo2))
        assert_equal([None], list(foo3))
        assert_equal(True, Foo.__iter__ == old, f"{Foo.__iter__} != {old}")

    def test_flexmock_should_mock_private_methods_with_leading_underscores(self):
        class ClassWithPrivateMethods:
            def __private_instance_method(self):
                pass

            @classmethod
            def __private_class_method(cls):
                # pylint: disable=unused-private-member
                # pylint bug https://github.com/PyCQA/pylint/issues/4681
                pass

            def instance_method(self):
                return self.__private_instance_method()

            @classmethod
            def class_method(cls):
                return cls.__private_class_method()

        # Instance
        instance = ClassWithPrivateMethods()
        flexmock(instance).should_receive("__private_instance_method").and_return("bar")
        assert_equal("bar", instance.instance_method())

        # Class
        flexmock(ClassWithPrivateMethods).should_receive("__private_class_method").and_return("baz")
        assert_equal("baz", ClassWithPrivateMethods.class_method())

    def test_flexmock_should_mock_generators(self):
        class Gen:
            def foo(self):
                pass

        gen = Gen()
        flexmock(gen).should_receive("foo").and_yield(*range(1, 10))
        output = list(gen.foo())
        assert_equal(list(range(1, 10)), output)

    def test_flexmock_should_verify_correct_spy_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return("real", "stuff")
        assert_equal(("real", "stuff"), user.get_stuff())

    def test_flexmock_should_verify_correct_spy_regexp_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return(
            re.compile("ea.*"), re.compile("^stuff$")
        )
        assert_equal(("real", "stuff"), user.get_stuff())

    def test_flexmock_should_verify_spy_raises_correct_exception_class(self):
        class FakeException(Exception):
            def __init__(self, param, param2):
                self.message = f"{param}, {param2}"
                Exception.__init__(self)

        class User:
            def get_stuff(self):
                raise FakeException(1, 2)

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FakeException, 1, 2)
        user.get_stuff()

    def test_flexmock_should_verify_spy_matches_exception_message(self):
        class FakeException(Exception):
            def __init__(self, param, param2):
                self.p1 = param
                self.p2 = param2
                Exception.__init__(self, param)

            def __str__(self):
                return f"{self.p1}, {self.p2}"

        class User:
            def get_stuff(self):
                raise FakeException("1", "2")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FakeException, "2", "1")
        with assert_raises(
            ExceptionMessageError,
            (
                "Error message mismatch with raised FakeException:\n"
                "  Expected message:\n\t'1, 2'\n"
                "  Received message:\n\t'2, 1'"
            ),
        ):
            user.get_stuff()

    def test_flexmock_should_verify_spy_matches_exception_regexp(self):
        class User:
            def get_stuff(self):
                raise Exception("123asdf345")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(Exception, re.compile("asdf"))
        user.get_stuff()
        self._tear_down()

    def test_flexmock_should_verify_spy_matches_exception_regexp_mismatch(self):
        class User:
            def get_stuff(self):
                raise Exception("123asdf345")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(Exception, re.compile("^asdf"))
        with assert_raises(
            ExceptionMessageError,
            (
                "Error message mismatch with raised Exception:\n"
                "  Expected pattern:\n\t/^asdf/\n"
                "  Received message:\n\t'123asdf345'"
            ),
        ):
            user.get_stuff()

    def test_flexmock_should_blow_up_on_wrong_spy_exception_type(self):
        class User:
            def get_stuff(self):
                raise CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(MethodCallError)
        with assert_raises(
            ExceptionClassError,
            (
                "Raised exception for call get_stuff did not match expectation:\n"
                "  Expected:\t<class 'flexmock.exceptions.MethodCallError'>\n"
                "  Raised:\t<class 'flexmock.exceptions.CallOrderError'>"
            ),
        ):
            user.get_stuff()

    def test_flexmock_should_match_spy_exception_parent_type(self):
        class User:
            def get_stuff(self):
                raise CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FlexmockError)
        user.get_stuff()

    def test_flexmock_should_reraise_exception_in_spy(self):
        class RaisesException:
            @classmethod
            def class_method(cls):
                raise RuntimeError("foo")

            @staticmethod
            def static_method():
                raise RuntimeError("bar")

            def instance_method(self):
                raise RuntimeError("baz")

        instance = RaisesException()
        flexmock(instance).should_call("class_method").once()
        flexmock(instance).should_call("static_method").once()
        flexmock(instance).should_call("instance_method").once()

        with assert_raises(RuntimeError, "foo"):
            instance.class_method()
        with assert_raises(RuntimeError, "bar"):
            instance.static_method()
        with assert_raises(RuntimeError, "baz"):
            instance.instance_method()

        flexmock(RaisesException).should_call("class_method").once()
        flexmock(RaisesException).should_call("static_method").once()
        with assert_raises(RuntimeError, "foo"):
            RaisesException.class_method()
        with assert_raises(RuntimeError, "bar"):
            RaisesException.static_method()

    def test_flexmock_should_reraise_exception_in_spy_with_return_values(self):
        class RaisesException:
            @classmethod
            def class_method(cls):
                raise RuntimeError("foo")

            @staticmethod
            def static_method():
                raise RuntimeError("bar")

            def instance_method(self):
                raise RuntimeError("baz")

        instance = RaisesException()
        flexmock(instance).should_call("class_method").and_return("foo").once()
        flexmock(instance).should_call("static_method").and_return("bar").once()
        flexmock(instance).should_call("instance_method").and_return("baz").once()

        with assert_raises(RuntimeError, "foo"):
            instance.class_method()
        with assert_raises(RuntimeError, "bar"):
            instance.static_method()
        with assert_raises(RuntimeError, "baz"):
            instance.instance_method()

        flexmock(RaisesException).should_call("class_method").once()
        flexmock(RaisesException).should_call("static_method").once()
        with assert_raises(RuntimeError, "foo"):
            RaisesException.class_method()
        with assert_raises(RuntimeError, "bar"):
            RaisesException.static_method()

    def test_and_raise_with_value_that_is_not_a_class(self):
        class RaisesException:
            def get_stuff(self):
                raise RuntimeError("baz")

        instance = RaisesException()
        flexmock(instance).should_call("get_stuff").and_raise(RuntimeError("foo")).once()
        with assert_raises(
            ExceptionClassError,
            re.compile(
                r"Raised exception for call get_stuff did not match expectation:\n"
                # Python 3.6 contains comma after 'foo'
                r"  Expected:\tRuntimeError\('foo',?\)\n"
                r"  Raised:\t<class 'RuntimeError'>\n\n"
                r"Did you try to call and_raise with an instance\?\n"
                r'Instead of and_raise\(Exception\("arg"\)\), try and_raise\(Exception, "arg"\)',
            ),
        ):
            instance.get_stuff()

    def test_flexmock_should_blow_up_on_wrong_spy_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

            def get_more_stuff(self):
                return "other", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return("other", "stuff")
        with assert_raises(
            MethodSignatureError,
            (
                "Returned values for call get_stuff did not match expectation:\n"
                "  Expected:\t('other', 'stuff')\n"
                "  Returned:\t('real', 'stuff')"
            ),
        ):
            user.get_stuff()
        flexmock(user).should_call("get_more_stuff").and_return()
        with assert_raises(
            MethodSignatureError,
            (
                "Returned values for call get_more_stuff did not match expectation:\n"
                "  Expected:\tNone\n"
                "  Returned:\t('other', 'stuff')"
            ),
        ):
            user.get_more_stuff()

    def test_flexmock_should_mock_same_class_twice(self):
        class Foo:
            pass

        flexmock(Foo)
        flexmock(Foo)

    def test_flexmock_spy_should_not_clobber_original_method(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff")
        flexmock(user).should_call("get_stuff")
        assert_equal(("real", "stuff"), user.get_stuff())

    def test_flexmock_should_properly_restore_static_methods(self):
        class User:
            @staticmethod
            def get_stuff():
                return "ok!"

        assert isinstance(User.__dict__["get_stuff"], staticmethod)
        assert_equal("ok!", User.get_stuff())
        flexmock(User).should_receive("get_stuff")
        assert User.get_stuff() is None
        self._tear_down()
        assert_equal("ok!", User.get_stuff())
        assert isinstance(User.__dict__["get_stuff"], staticmethod)

    def test_flexmock_should_properly_restore_undecorated_static_methods(self):
        class User:
            def get_stuff():
                return "ok!"

            get_stuff = staticmethod(get_stuff)  # pylint: disable=no-staticmethod-decorator

        assert_equal("ok!", User.get_stuff())
        flexmock(User).should_receive("get_stuff")
        assert User.get_stuff() is None
        self._tear_down()
        assert_equal("ok!", User.get_stuff())

    def test_flexmock_should_properly_restore_module_level_functions(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod).should_receive("module_level_function").with_args(1, 2)
        assert_equal(None, module_level_function(1, 2))
        self._tear_down()
        assert_equal("1, 2", module_level_function(1, 2))

    def test_module_level_function_with_kwargs(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod).should_receive("module_level_function").with_args(1, args="expected")
        with assert_raises(
            FlexmockError,
            (
                "Arguments for call module_level_function did not match expectations:\n"
                '  Received call:\tmodule_level_function(1, args="not expected")\n'
                '  Expected call[1]:\tmodule_level_function(args="expected", some=1)'
            ),
        ):
            module_level_function(1, args="not expected")

    def test_flexmock_should_support_mocking_classes_as_functions(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod).should_receive("SomeClass").and_return("yay")
        assert_equal("yay", SomeClass())

    def test_flexmock_should_properly_restore_class_methods(self):
        class User:
            @classmethod
            def get_stuff(cls):
                return cls.__name__

        assert isinstance(User.__dict__["get_stuff"], classmethod)
        assert_equal("User", User.get_stuff())
        flexmock(User).should_receive("get_stuff").and_return("foo")
        assert_equal("foo", User.get_stuff())
        self._tear_down()
        assert_equal("User", User.get_stuff())
        assert isinstance(User.__dict__["get_stuff"], classmethod)

    def test_spy_should_match_return_value_class(self):
        class User:
            pass

        user = User()
        foo = flexmock(
            foo=lambda: ("bar", "baz"),
            bar=lambda: user,
            baz=lambda: None,
            bax=lambda: None,
        )
        foo.should_call("foo").and_return(str, str)
        foo.should_call("bar").and_return(User)
        foo.should_call("baz").and_return(object)
        foo.should_call("bax").and_return(None)
        assert_equal(("bar", "baz"), foo.foo())
        assert_equal(user, foo.bar())
        assert_equal(None, foo.baz())
        assert_equal(None, foo.bax())

    def test_spy_should_not_match_falsy_stuff(self):
        class Foo:
            def foo(self):
                return None

            def bar(self):
                return False

            def baz(self):
                return []

            def quux(self):
                return ""

        foo = Foo()
        flexmock(foo).should_call("foo").and_return("bar").once()
        flexmock(foo).should_call("bar").and_return("bar").once()
        flexmock(foo).should_call("baz").and_return("bar").once()
        flexmock(foo).should_call("quux").and_return("bar").once()
        with assert_raises(
            FlexmockError,
            (
                "Returned values for call foo did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\tNone"
            ),
        ):
            foo.foo()
        with assert_raises(
            FlexmockError,
            (
                "Returned values for call bar did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\tFalse"
            ),
        ):
            foo.bar()
        with assert_raises(
            FlexmockError,
            (
                "Returned values for call baz did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\t[]"
            ),
        ):
            foo.baz()
        with assert_raises(
            FlexmockError,
            (
                "Returned values for call quux did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\t''"
            ),
        ):
            foo.quux()

    def test_new_instances_should_blow_up_on_should_receive(self):
        class User:
            pass

        mock = flexmock(User).new_instances(None).mock
        with assert_raises(FlexmockError, "User does not have attribute 'foo'"):
            mock.should_receive("foo")

    def test_should_call_alias_should_create_a_spy(self):
        class Foo:
            def get_stuff(self):
                return "yay"

        foo = Foo()
        flexmock(foo).should_call("get_stuff").and_return("yay").once()
        with assert_raises(
            MethodCallError, "get_stuff() expected to be called exactly 1 time, called 0 times"
        ):
            self._tear_down()

    def test_flexmock_should_fail_mocking_nonexistent_methods(self):
        class User:
            pass

        user = User()
        with assert_raises(
            FlexmockError,
            re.compile(
                r"<.+\.<locals>\.User object at 0x.+> does not have attribute 'nonexistent'"
            ),
        ):
            flexmock(user).should_receive("nonexistent")

    def test_flexmock_should_not_explode_on_unicode_formatting(self):
        formatted = _format_args("method", {"kargs": (chr(0x86C7),), "kwargs": {}})
        assert_equal('method("蛇")', formatted)

    def test_return_value_should_not_explode_on_unicode_values(self):
        return_value = ReturnValue(chr(0x86C7))
        assert_equal('"蛇"', f"{return_value}")
        return_value = ReturnValue((chr(0x86C7), chr(0x86C7)))
        assert_equal('("蛇", "蛇")', f"{return_value}")

    def test_pass_thru_should_call_original_method_only_once(self):
        class Nyan:
            def __init__(self):
                self.n = 0

            def method(self):
                self.n += 1

        obj = Nyan()
        flexmock(obj)
        obj.should_call("method")
        obj.method()
        assert_equal(obj.n, 1)

    def test_should_call_works_for_same_method_with_different_args(self):
        class Foo:
            def method(self, arg):
                pass

        foo = Foo()
        flexmock(foo).should_call("method").with_args("foo").once()
        flexmock(foo).should_call("method").with_args("bar").once()
        foo.method("foo")
        foo.method("bar")
        self._tear_down()

    def test_should_call_fails_properly_for_same_method_with_different_args(self):
        class Foo:
            def method(self, arg):
                pass

        foo = Foo()
        flexmock(foo).should_call("method").with_args("foo").once()
        flexmock(foo).should_call("method").with_args("bar").once()
        foo.method("foo")
        with assert_raises(
            MethodCallError,
            'method(arg="bar") expected to be called exactly 1 time, called 0 times',
        ):
            self._tear_down()

    def test_should_give_reasonable_error_for_builtins(self):
        with assert_raises(
            MockBuiltinError,
            (
                "Python does not allow you to mock builtin objects or modules. "
                "Consider wrapping it in a class you can mock instead"
            ),
        ):
            flexmock(object)

    def test_should_give_reasonable_error_for_instances_of_builtins(self):
        with assert_raises(
            MockBuiltinError,
            (
                "Python does not allow you to mock instances of builtin objects. "
                "Consider wrapping it in a class you can mock instead"
            ),
        ):
            flexmock(object())

    def test_mock_chained_method_calls_works_with_one_level(self):
        class Foo:
            def method2(self):
                return "foo"

        class Bar:
            def method1(self):
                return Foo()

        foo = Bar()
        assert_equal("foo", foo.method1().method2())
        flexmock(foo).should_receive("method1.method2").and_return("bar")
        assert_equal("bar", foo.method1().method2())

    def test_mock_chained_method_supports_args_and_mocks(self):
        class Foo:
            def method2(self, arg):
                return arg

        class Bar:
            def method1(self):
                return Foo()

        foo = Bar()
        assert_equal("foo", foo.method1().method2("foo"))
        flexmock(foo).should_receive("method1.method2").with_args("foo").and_return("bar").once()
        assert_equal("bar", foo.method1().method2("foo"))
        self._tear_down()
        flexmock(foo).should_receive("method1.method2").with_args("foo").and_return("bar").once()
        with assert_raises(
            MethodCallError, 'method2("foo") expected to be called exactly 1 time, called 0 times'
        ):
            self._tear_down()

    def test_mock_chained_method_calls_works_with_more_than_one_level(self):
        class Baz:
            def method3(self):
                return "foo"

        class Foo:
            def method2(self):
                return Baz()

        class Bar:
            def method1(self):
                return Foo()

        foo = Bar()
        assert_equal("foo", foo.method1().method2().method3())
        flexmock(foo).should_receive("method1.method2.method3").and_return("bar")
        assert_equal("bar", foo.method1().method2().method3())

    def test_flexmock_should_replace_method(self):
        class Foo:
            def method(self, arg):
                return arg

        foo = Foo()
        flexmock(foo).should_receive("method").replace_with(lambda x: x == 5)
        assert_equal(foo.method(5), True)
        assert_equal(foo.method(4), False)

    def test_flexmock_should_replace_cannot_be_specified_twice(self):
        class Foo:
            def method(self, arg):
                return arg

        foo = Foo()
        expectation = flexmock(foo).should_receive("method").replace_with(lambda x: x == 5)
        with assert_raises(FlexmockError, "replace_with cannot be specified twice"):
            expectation.replace_with(lambda x: x == 3)

    def test_flexmock_should_mock_the_same_method_multiple_times(self):
        class Foo:
            def method(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method").and_return(1)
        assert_equal(foo.method(), 1)
        flexmock(foo).should_receive("method").and_return(2)
        assert_equal(foo.method(), 2)
        flexmock(foo).should_receive("method").and_return(3)
        assert_equal(foo.method(), 3)
        flexmock(foo).should_receive("method").and_return(4)
        assert_equal(foo.method(), 4)

    def test_new_instances_should_be_a_method(self):
        class Foo:
            pass

        flexmock(Foo).new_instances("bar")
        assert_equal("bar", Foo())
        self._tear_down()
        assert Foo() != "bar"

    def test_new_instances_raises_error_when_not_a_class(self):
        class Foo:
            pass

        foo = Foo()
        flexmock(foo)
        with assert_raises(FlexmockError, "new_instances can only be called on a class mock"):
            foo.new_instances("bar")

    def test_new_instances_works_with_multiple_return_values(self):
        class Foo:
            pass

        flexmock(Foo).new_instances("foo", "bar")
        assert_equal("foo", Foo())
        assert_equal("bar", Foo())

    def test_should_receive_should_not_replace_flexmock_methods(self):
        class Foo:
            def bar(self):
                pass

        foo = Foo()
        flexmock(foo)
        for method_name in ["should_receive", "should_call", "new_instances"]:
            with assert_raises(FlexmockError, "unable to replace flexmock methods"):
                foo.should_receive(method_name)

    def test_flexmock_should_not_add_methods_if_they_already_exist(self):
        class Foo:
            def should_receive(self):
                return "real"

            def bar(self):
                pass

        foo = Foo()
        mock = flexmock(foo)
        assert_equal(foo.should_receive(), "real")
        assert "should_call" not in dir(foo)
        assert "new_instances" not in dir(foo)
        mock.should_receive("bar").and_return("baz")
        assert_equal(foo.bar(), "baz")
        self._tear_down()
        assert_equal(foo.should_receive(), "real")

    def test_flexmock_should_not_add_class_methods_if_they_already_exist(self):
        class Foo:
            def should_receive(self):
                return "real"

            def bar(self):
                pass

        foo = Foo()
        mock = flexmock(Foo)
        assert_equal(foo.should_receive(), "real")
        assert "should_call" not in dir(Foo)
        assert "new_instances" not in dir(Foo)
        mock.should_receive("bar").and_return("baz")
        assert_equal(foo.bar(), "baz")
        self._tear_down()
        assert_equal(foo.should_receive(), "real")

    def test_expectation_properties_work_with_parens(self):
        foo = flexmock().should_receive("bar").at_least().once().and_return("baz").mock()
        assert_equal("baz", foo.bar())

    def test_mocking_down_the_inheritance_chain_class_to_class(self):
        class Parent:
            def foo(self):
                pass

        class Child(Parent):
            def bar(self):
                pass

        flexmock(Parent).should_receive("foo").and_return("outer")
        flexmock(Child).should_receive("bar").and_return("inner")
        assert Parent().foo() == "outer"
        assert Child().bar() == "inner"

    def test_arg_matching_works_with_regexp(self):
        class Foo:
            def foo(self, arg1, arg2):
                pass

        foo = Foo()
        flexmock(foo).should_receive("foo").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("f")
        ).and_return("mocked")
        assert_equal("mocked", foo.foo("arg1somejunkasdf", arg2="aadsfdas"))

    def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_karg(self):
        class Foo:
            def foo(self, arg1, arg2):
                pass

        foo = Foo()
        flexmock(foo).should_receive("foo").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("a")
        ).and_return("mocked")
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call foo did not match expectations:\n"
                '  Received call:\tfoo("arg1somejunkasdfa", arg2="a")\n'
                "  Expected call[1]:\tfoo(arg2=/a/, arg1=/^arg1.*asdf$/)"
            ),
        ):
            foo.foo("arg1somejunkasdfa", arg2="a")

    def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_kwarg(self):
        class Foo:
            def foo(self, arg1, arg2):
                pass

        foo = Foo()
        flexmock(foo).should_receive("foo").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("a")
        ).and_return("mocked")
        with assert_raises(
            MethodSignatureError,
            (
                "Arguments for call foo did not match expectations:\n"
                '  Received call:\tfoo("arg1somejunkasdf", arg2="b")\n'
                "  Expected call[1]:\tfoo(arg2=/a/, arg1=/^arg1.*asdf$/)"
            ),
        ):
            foo.foo("arg1somejunkasdf", arg2="b")

    def test_flexmock_class_returns_same_object_on_repeated_calls(self):
        class Foo:
            pass

        a = flexmock(Foo)
        b = flexmock(Foo)
        assert_equal(a, b)

    def test_flexmock_object_returns_same_object_on_repeated_calls(self):
        class Foo:
            pass

        foo = Foo()
        a = flexmock(foo)
        b = flexmock(foo)
        assert_equal(a, b)

    def test_flexmock_ordered_worked_after_default_stub(self):
        foo = flexmock()
        foo.should_receive("bar")
        foo.should_receive("bar").with_args("a").ordered()
        foo.should_receive("bar").with_args("b").ordered()
        with assert_raises(CallOrderError, 'bar("b") called before bar("a")'):
            foo.bar("b")

    def test_flexmock_ordered_works_with_same_args(self):
        foo = flexmock()
        foo.should_receive("bar").ordered().and_return(1)
        foo.should_receive("bar").ordered().and_return(2)
        a = foo.bar()
        assert_equal(a, 1)
        b = foo.bar()
        assert_equal(b, 2)

    def test_flexmock_ordered_works_with_same_args_after_default_stub(self):
        foo = flexmock()
        foo.should_receive("bar").and_return(9)
        foo.should_receive("bar").ordered().and_return(1)
        foo.should_receive("bar").ordered().and_return(2)
        a = foo.bar()
        assert_equal(a, 1)
        b = foo.bar()
        assert_equal(b, 2)
        c = foo.bar()
        assert_equal(c, 9)

    def test_state_machine(self):
        class Radio:
            def __init__(self):
                self.is_on = False
                self.volume = 0

            def switch_on(self):
                self.is_on = True

            def switch_off(self):
                self.is_on = False

            def select_channel(self):
                return None

            def adjust_volume(self, num):
                self.volume = num

        radio = Radio()
        flexmock(radio)

        def radio_is_on():
            return radio.is_on

        radio.should_receive("select_channel").once().when(lambda: radio.is_on)
        radio.should_call("adjust_volume").once().with_args(5).when(radio_is_on)

        with assert_raises(
            StateError, "select_channel expected to be called when lambda: radio.is_on is True"
        ):
            radio.select_channel()
        with assert_raises(
            StateError, "adjust_volume expected to be called when radio_is_on is True"
        ):
            radio.adjust_volume(5)
        radio.is_on = True
        radio.select_channel()
        radio.adjust_volume(5)

    def test_when_parameter_should_be_callable(self):
        with assert_raises(FlexmockError, "when() parameter must be callable"):
            flexmock().should_receive("something").when(1)

    def test_flexmock_should_not_blow_up_with_builtin_in_when(self):
        # It is not possible to get source for builtins. Flexmock should handle
        # this gracefully.
        mock = flexmock()
        mock.should_receive("something").when(functools.partial(lambda: False))
        with assert_raises(StateError, "something expected to be called when condition is True"):
            # Should not raise TypeError
            mock.something()

    def test_support_at_least_and_at_most_together(self):
        class Foo:
            def bar(self):
                pass

        foo = Foo()
        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        with assert_raises(
            MethodCallError,
            "bar() expected to be called at least 1 time and at most 2 times, called 0 times",
        ):
            self._tear_down()

        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        foo.bar()
        foo.bar()
        with assert_raises(
            MethodCallError, "bar() expected to be called at most 2 times, called 3 times"
        ):
            foo.bar()

        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        foo.bar()
        self._tear_down()

        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        foo.bar()
        foo.bar()
        self._tear_down()

    def test_at_least_cannot_be_used_twice(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        with assert_raises(FlexmockError, "cannot use at_least modifier twice"):
            expectation.at_least().at_least()

    def test_at_most_cannot_be_used_twice(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        with assert_raises(FlexmockError, "cannot use at_most modifier twice"):
            expectation.at_most().at_most()

    def test_at_least_cannot_be_specified_until_at_most_is_set(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        with assert_raises(FlexmockError, "cannot use at_most with at_least unset"):
            expectation.at_least().at_most()

    def test_at_most_cannot_be_specified_until_at_least_is_set(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        with assert_raises(FlexmockError, "cannot use at_least with at_most unset"):
            expectation.at_most().at_least()

    def test_proper_reset_of_subclass_methods(self):
        class A:
            def x(self):
                return "a"

        class B(A):
            def x(self):
                return "b"

        flexmock(B).should_receive("x").and_return("1")
        self._tear_down()
        assert_equal("b", B().x())

    def test_format_args_supports_tuples(self):
        formatted = _format_args("method", {"kargs": ((1, 2),), "kwargs": {}})
        assert_equal("method((1, 2))", formatted)

    def test_mocking_subclass_of_str(self):
        class String(str):
            pass

        s = String()
        flexmock(s, endswith="fake")
        assert_equal("fake", s.endswith("stuff"))
        self._tear_down()
        assert_equal(False, s.endswith("stuff"))

    def test_ordered_on_different_methods(self):
        class String(str):
            pass

        s = String("abc")
        flexmock(s)
        s.should_call("startswith").with_args("asdf", 0, 4).ordered()
        s.should_call("endswith").ordered()
        with assert_raises(
            CallOrderError,
            re.compile(
                r'endswith\("c"\) called before startswith'
                # Argument names are displayed in PyPy
                r'\((prefix=)?"asdf", (start=)?0, (end=)?4\)'
            ),
        ):
            s.endswith("c")

    def test_fake_object_takes_properties(self):
        foo = flexmock(bar=property(lambda self: "baz"))
        bar = flexmock(foo=property(lambda self: "baz"))
        assert_equal("baz", foo.bar)
        assert_equal("baz", bar.foo)

    def test_replace_non_callable_class_attributes(self):
        class Foo:
            bar = 1

        foo = Foo()
        bar = Foo()
        flexmock(foo, bar=2)
        assert_equal(2, foo.bar)
        assert_equal(1, bar.bar)
        self._tear_down()
        assert_equal(1, foo.bar)

    def test_should_chain_attributes(self):
        class Baz:
            x = 1

        class Bar:
            baz = Baz()

        class Foo:
            bar = Bar()

        foo = Foo()
        foo = flexmock(foo)
        foo.should_receive("bar.baz.x").and_return(2)
        assert_equal(2, foo.bar.baz.x)
        self._tear_down()
        assert_equal(1, foo.bar.baz.x)

    def test_replace_non_callable_instance_attributes(self):
        class Foo:
            def __init__(self):
                self.bar = 1

        foo = Foo()
        bar = Foo()
        flexmock(foo, bar=2)
        flexmock(bar, bar=1)
        assert_equal(2, foo.bar)
        self._tear_down()
        assert_equal(1, foo.bar)

    def test_replace_non_callable_module_attributes(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod, MODULE_LEVEL_ATTRIBUTE="yay")
        assert_equal("yay", MODULE_LEVEL_ATTRIBUTE)
        self._tear_down()
        assert_equal("test", MODULE_LEVEL_ATTRIBUTE)

    def test_non_callable_attributes_fail_to_set_expectations(self):
        class Foo:
            bar = 1

        foo = Foo()
        e = flexmock(foo).should_receive("bar").and_return(2)
        with assert_raises(FlexmockError, "can't use times() with attribute stubs"):
            e.times(1)
        with assert_raises(FlexmockError, "can't use with_args() with attribute stubs"):
            e.with_args(())
        with assert_raises(FlexmockError, "can't use replace_with() with attribute/property stubs"):
            e.replace_with(lambda x: x)
        with assert_raises(FlexmockError, "can't use and_raise() with attribute stubs"):
            e.and_raise(Exception)
        with assert_raises(FlexmockError, "can't use when() with attribute stubs"):
            e.when(lambda x: x)
        with assert_raises(FlexmockError, "can't use and_yield() with attribute stubs"):
            e.and_yield(1)
        with assert_raises(FlexmockError, "can't use ordered() with attribute stubs"):
            object.__getattribute__(e, "ordered")()
        with assert_raises(FlexmockError, "can't use at_least() with attribute stubs"):
            object.__getattribute__(e, "at_least")()
        with assert_raises(FlexmockError, "can't use at_most() with attribute stubs"):
            object.__getattribute__(e, "at_most")()
        with assert_raises(FlexmockError, "can't use one_by_one() with attribute stubs"):
            object.__getattribute__(e, "one_by_one")()

    def test_and_return_defaults_to_none_with_no_arguments(self):
        foo = flexmock()
        foo.should_receive("bar").and_return()
        assert_equal(None, foo.bar())

    def test_should_replace_attributes_that_are_instances_of_classes(self):
        class Foo:
            pass

        class Bar:
            foo = Foo()

        bar = Bar()
        flexmock(bar, foo="test")
        assert_equal("test", bar.foo)

    def test_isproperty(self):
        class Foo:
            @property
            def bar(self):
                pass

            def baz(self):
                pass

        class Bar(Foo):
            pass

        foo = Foo()
        bar = Bar()
        assert_equal(True, _isproperty(foo, "bar"))
        assert_equal(False, _isproperty(foo, "baz"))
        assert_equal(True, _isproperty(Foo, "bar"))
        assert_equal(False, _isproperty(Foo, "baz"))
        assert_equal(True, _isproperty(bar, "bar"))
        assert_equal(False, _isproperty(bar, "baz"))
        assert_equal(True, _isproperty(Bar, "bar"))
        assert_equal(False, _isproperty(Bar, "baz"))
        assert_equal(False, _isproperty(Mock(), "baz"))

    def test_fake_object_supporting_iteration(self):
        foo = flexmock()
        foo.should_receive("__iter__").and_yield(1, 2, 3)
        assert_equal([1, 2, 3], list(foo))

    def test_with_args_for_single_named_arg_with_optional_args(self):
        class Foo:
            def bar(self, one, two="optional"):
                pass

        e = flexmock(Foo).should_receive("bar")
        e.with_args(one=1)

    def test_with_args_doesnt_set_max_when_using_varargs(self):
        class Foo:
            def bar(self, *kargs):
                pass

        flexmock(Foo).should_receive("bar").with_args(1, 2, 3)

    def test_with_args_doesnt_set_max_when_using_kwargs(self):
        class Foo:
            def bar(self, **kwargs):
                pass

        flexmock(Foo).should_receive("bar").with_args(1, 2, 3)

    def test_with_args_blows_up_on_too_few_args(self):
        class Foo:
            def foo(self, a):
                pass

            def bar(self, a, b, c=1):
                pass

        mock = flexmock(Foo)
        e1 = mock.should_receive("foo")
        e2 = mock.should_receive("bar")
        with assert_raises(
            MethodSignatureError, "foo requires at least 1 argument, expectation provided 0"
        ):
            e1.with_args()
        with assert_raises(
            MethodSignatureError, "bar requires at least 2 arguments, expectation provided 1"
        ):
            e2.with_args(1)

    def test_with_args_blows_up_on_too_few_args_with_kwargs(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        with assert_raises(
            MethodSignatureError, "bar requires at least 3 arguments, expectation provided 2"
        ):
            e.with_args(1, c=2)

    def test_with_args_blows_up_on_too_many_args(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        with assert_raises(
            MethodSignatureError, "bar requires at most 3 arguments, expectation provided 4"
        ):
            e.with_args(1, 2, 3, 4)

    def test_with_args_blows_up_on_kwarg_overlapping_positional(self):
        class Foo:
            def bar(self, a, b, c=1, **kwargs):
                pass

        e = flexmock(Foo).should_receive("bar")
        with assert_raises(
            MethodSignatureError, "['c'] already given as positional argument to bar"
        ):
            e.with_args(1, 2, 3, c=2)
        with assert_raises(
            MethodSignatureError, "['c', 'b'] already given as positional arguments to bar"
        ):
            e.with_args(1, 2, 3, c=2, b=3)

    def test_with_args_blows_up_on_invalid_kwarg(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        with assert_raises(MethodSignatureError, "d is not a valid keyword argument to bar"):
            e.with_args(1, 2, d=2)

    def test_with_args_ignores_invalid_args_on_flexmock_instances(self):
        foo = flexmock(bar=lambda x: x)
        foo.should_receive("bar").with_args("stuff")
        foo.bar("stuff")

    def test_with_args_does_not_compensate_for_self_on_static_instance_methods(self):
        class Foo:
            @staticmethod
            def bar(x):
                pass

        foo = Foo()
        flexmock(foo).should_receive("bar").with_args("stuff")
        foo.bar("stuff")

    def test_with_args_does_not_compensate_for_self_on_static_class_methods(self):
        class Foo:
            @staticmethod
            def bar(x):
                pass

        flexmock(Foo).should_receive("bar").with_args("stuff")
        Foo.bar("stuff")

    def test_with_args_does_compensate_for_cls_on_class_methods(self):
        class Foo:
            @classmethod
            def bar(cls, x):
                pass

        foo = Foo()
        flexmock(foo).should_receive("bar").with_args("stuff")
        foo.bar("stuff")

    def test_calling_with_keyword_args_matches_mock_with_positional_args(self):
        class Foo:
            def bar(self, a, b, c):
                pass

        foo = Foo()
        flexmock(foo).should_receive("bar").with_args(1, 2, 3).once()
        foo.bar(a=1, b=2, c=3)

    def test_calling_with_positional_args_matches_mock_with_kwargs(self):
        class Foo:
            def bar(self, a, b, c):
                pass

        foo = Foo()
        flexmock(foo).should_receive("bar").with_args(a=1, b=2, c=3).once()
        foo.bar(1, 2, c=3)

    def test_use_replace_with_for_callable_shortcut_kwargs(self):
        class Foo:
            def bar(self):
                return "bar"

        foo = Foo()
        flexmock(foo, bar=lambda: "baz")
        assert_equal("baz", foo.bar())

    def test_mock_multiple_properties(self):
        class Foo:
            @property
            def prop1(self):
                return "prop1"

            @property
            def prop2(self):
                return "prop2"

        mocked = Foo()
        flexmock(mocked, prop1="mocked1", prop2="mocked2")
        assert_equal("mocked1", mocked.prop1)
        assert_equal("mocked2", mocked.prop2)

    def test_mock_property_with_attribute_on_instance(self):
        class Foo:
            @property
            def bar(self):
                return "bar"

        foo = Foo()
        foo2 = Foo()
        foo3 = Foo()
        flexmock(foo, bar="baz")
        flexmock(foo2, bar="baz2")
        assert_equal("baz", foo.bar)
        assert_equal("baz2", foo2.bar)
        assert_equal("bar", foo3.bar)
        self._tear_down()
        assert_equal(False, hasattr(Foo, "_flexmock__bar"), "Property bar not cleaned up")
        assert_equal("bar", foo.bar)
        assert_equal("bar", foo2.bar)
        assert_equal("bar", foo3.bar)

    def test_mock_property_with_attribute_on_class(self):
        class Foo:
            @property
            def bar(self):
                return "bar"

        foo = Foo()
        foo2 = Foo()
        flexmock(Foo, bar="baz")
        assert_equal("baz", foo.bar)
        assert_equal("baz", foo2.bar)
        self._tear_down()
        assert_equal(False, hasattr(Foo, "_flexmock__bar"), "Property bar not cleaned up")
        assert_equal("bar", foo.bar)
        assert_equal("bar", foo2.bar)

    def test_verifying_methods_when_mocking_module(self):
        # previously, we had problems with recognizing methods vs functions if the mocked
        # object was an imported module
        flexmock(some_module).should_receive("ModuleClass").with_args(1, 2)
        flexmock(some_module).should_receive("module_function").with_args(1, 2)

    def test_is_class_method(self):
        assert _is_class_method(SomeClass.class_method, "class_method") is True
        assert _is_class_method(SomeClass.static_method, "static_method") is False
        assert _is_class_method(SomeClass.instance_method, "instance_method") is False
        # Method names do no match
        assert _is_class_method(SomeClass.class_method, "other_method") is False

        some_class = SomeClass()
        assert _is_class_method(some_class.class_method, "class_method") is True
        assert _is_class_method(some_class.static_method, "static_method") is False
        assert _is_class_method(some_class.instance_method, "instance_method") is False

        assert _is_class_method(DerivedClass.class_method, "class_method") is True
        assert _is_class_method(DerivedClass.static_method, "static_method") is False
        assert _is_class_method(DerivedClass.instance_method, "instance_method") is False

        derived_class = DerivedClass()
        assert _is_class_method(derived_class.class_method, "class_method") is True
        assert _is_class_method(derived_class.static_method, "static_method") is False
        assert _is_class_method(derived_class.instance_method, "instance_method") is False

    def test_is_class_method_proxied(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        assert _is_class_method(SomeClassProxy.class_method, "class_method") is True
        assert _is_class_method(SomeClassProxy.static_method, "static_method") is False
        assert _is_class_method(SomeClassProxy.instance_method, "instance_method") is False

        some_class = SomeClassProxy()
        assert _is_class_method(some_class.class_method, "class_method") is True
        assert _is_class_method(some_class.static_method, "static_method") is False
        assert _is_class_method(some_class.instance_method, "instance_method") is False

        DerivedClassProxy = Proxy(DerivedClass)
        assert _is_class_method(DerivedClassProxy.class_method, "class_method") is True
        assert _is_class_method(DerivedClassProxy.static_method, "static_method") is False
        assert _is_class_method(DerivedClassProxy.instance_method, "instance_method") is False

        derived_class = DerivedClassProxy()
        assert _is_class_method(derived_class.class_method, "class_method") is True
        assert _is_class_method(derived_class.static_method, "static_method") is False
        assert _is_class_method(derived_class.instance_method, "instance_method") is False

    def test_is_static_method(self):
        assert _is_static_method(SomeClass, "class_method") is False
        assert _is_static_method(SomeClass, "static_method") is True
        assert _is_static_method(SomeClass, "instance_method") is False

        some_class = SomeClass()
        assert _is_static_method(some_class, "class_method") is False
        assert _is_static_method(some_class, "static_method") is True
        assert _is_static_method(some_class, "instance_method") is False

        assert _is_static_method(DerivedClass, "class_method") is False
        assert _is_static_method(DerivedClass, "static_method") is True
        assert _is_static_method(DerivedClass, "instance_method") is False

        derived_class = DerivedClass()
        assert _is_static_method(derived_class, "class_method") is False
        assert _is_static_method(derived_class, "static_method") is True
        assert _is_static_method(derived_class, "instance_method") is False

    def test_is_static_method_proxied(self):
        # pylint: disable=not-callable
        SomeClassProxy = Proxy(SomeClass)
        assert _is_static_method(SomeClassProxy, "class_method") is False
        assert _is_static_method(SomeClassProxy, "static_method") is True
        assert _is_static_method(SomeClassProxy, "instance_method") is False

        some_class = SomeClassProxy()
        assert _is_static_method(some_class, "class_method") is False
        assert _is_static_method(some_class, "static_method") is True
        assert _is_static_method(some_class, "instance_method") is False

        DerivedClassProxy = Proxy(DerivedClass)
        assert _is_static_method(DerivedClassProxy, "class_method") is False
        assert _is_static_method(DerivedClassProxy, "static_method") is True
        assert _is_static_method(DerivedClassProxy, "instance_method") is False

        derived_class = DerivedClassProxy()
        assert _is_static_method(derived_class, "class_method") is False
        assert _is_static_method(derived_class, "static_method") is True
        assert _is_static_method(derived_class, "instance_method") is False


class TestFlexmockUnittest(RegularClass, unittest.TestCase):
    def tearDown(self):
        pass

    def _tear_down(self):
        return flexmock_teardown()


class ModernClass:
    """Contains features only available in 2.6 and above."""

    def test_context_manager_on_instance(self):
        class CM:
            def __enter__(self):
                pass

            def __exit__(self, *_):
                pass

        cm = CM()
        flexmock(cm).should_call("__enter__").once()
        flexmock(cm).should_call("__exit__").once()
        with cm:
            pass
        self._tear_down()

    def test_context_manager_on_class(self):
        class CM:
            def __enter__(self):
                pass

            def __exit__(self, *_):
                pass

        cm = CM()
        flexmock(CM).should_receive("__enter__").once()
        flexmock(CM).should_receive("__exit__").once()
        with cm:
            pass
        self._tear_down()

    def test_flexmock_should_support_with(self):
        foo = flexmock()
        with foo as mock:
            mock.should_receive("bar").and_return("baz")
        assert foo.bar() == "baz"

    def test_builtin_open(self):
        mock = flexmock(sys.modules["builtins"])
        fake_fd = flexmock(read=lambda: "some data")
        mock.should_receive("open").once.with_args("file_name").and_return(fake_fd)
        with open("file_name") as f:  # pylint: disable=unspecified-encoding
            data = f.read()
        self.assertEqual("some data", data)


class TestFlexmockUnittestModern(ModernClass, unittest.TestCase):
    def _tear_down(self):
        return unittest.TestCase.tearDown(self)


class TestUnittestModern(TestFlexmockUnittestModern):
    pass


class TestPy3Features(unittest.TestCase):
    def test_mock_kwargs_only_func_mock_all(self):
        flexmock(some_module).should_receive("kwargs_only_func1").with_args(
            1, bar=2, baz=3
        ).and_return(123)
        self.assertEqual(some_module.kwargs_only_func1(1, bar=2, baz=3), 123)

    def test_mock_kwargs_only_func_mock_required(self):
        flexmock(some_module).should_receive("kwargs_only_func1").with_args(1, bar=2).and_return(
            123
        )
        self.assertEqual(some_module.kwargs_only_func1(1, bar=2), 123)

    def test_mock_kwargs_only_func_fails_if_required_not_provided(self):
        with assert_raises(
            MethodSignatureError, 'kwargs_only_func1 requires keyword-only argument "bar"'
        ):
            flexmock(some_module).should_receive("kwargs_only_func1").with_args(1)
        with assert_raises(
            MethodSignatureError, 'kwargs_only_func2 requires keyword-only arguments "bar", "baz"'
        ):
            flexmock(some_module).should_receive("kwargs_only_func2").with_args(2)


class TestReturnValue(unittest.TestCase):
    def test_return_value_to_str(self):
        r_val = ReturnValue(value=1)
        assert str(r_val) == "1"

        r_val = ReturnValue(value=(1,))
        assert str(r_val) == "1"

        r_val = ReturnValue(value=(1, 2))
        assert str(r_val) == "(1, 2)"

        r_val = ReturnValue(value=1, raises=RuntimeError)
        assert str(r_val) == "<class 'RuntimeError'>(1)"


if __name__ == "__main__":
    unittest.main()
