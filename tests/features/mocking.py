"""Tests for flexmock mocking feature."""
# pylint: disable=missing-docstring,no-self-use,no-member,too-many-lines
import os
import random
import re
import sys

from flexmock import exceptions, flexmock
from flexmock._api import AT_LEAST, AT_MOST, EXACTLY, FlexmockContainer, Mock, flexmock_teardown
from tests import some_module
from tests.utils import assert_raises


class MockingTestCase:
    def test_print_expectation(self):
        mock = flexmock()
        expectation = mock.should_receive("foo")
        assert str(expectation) == "foo() -> ()"

    def test_flexmock_should_create_mock_object(self):
        mock = flexmock()
        assert isinstance(mock, Mock)

    def test_flexmock_should_create_mock_object_from_dict(self):
        mock = flexmock(foo="foo", bar="bar")
        assert mock.foo == "foo"
        assert mock.bar == "bar"

    def test_flexmock_should_add_expectations(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert "method_foo" in [x._name for x in FlexmockContainer.flexmock_objects[mock]]

    def test_flexmock_should_return_value(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar")
        mock.should_receive("method_bar").and_return("value_baz")
        assert mock.method_foo() == "value_bar"
        assert mock.method_bar() == "value_baz"

    def test_calling_deprecated_properties_should_raise_exception(self):
        error_msg = "Calling once, twice, never, or mock without parentheses has been deprecated"
        mock = flexmock()
        mock.should_receive("foo").once  # pylint: disable=expression-not-assigned
        with assert_raises(exceptions.FlexmockError, error_msg):
            flexmock_teardown()
        mock.should_receive("foo").twice  # pylint: disable=expression-not-assigned
        with assert_raises(exceptions.FlexmockError, error_msg):
            flexmock_teardown()
        mock.should_receive("foo").never  # pylint: disable=expression-not-assigned
        with assert_raises(exceptions.FlexmockError, error_msg):
            flexmock_teardown()
        mock.should_receive("foo").mock  # pylint: disable=expression-not-assigned
        with assert_raises(exceptions.FlexmockError, error_msg):
            flexmock_teardown()

    def test_type_flexmock_with_unicode_string_in_should_receive(self):
        class Foo:
            def method(self):
                return "bar"

        flexmock(Foo).should_receive("method").and_return("mocked_bar")

        instance = Foo()
        assert instance.method() == "mocked_bar"

    def test_flexmock_should_accept_shortcuts_for_creating_mock_object(self):
        mock = flexmock(attr1="value 1", attr2=lambda: "returning 2")
        assert mock.attr1 == "value 1"
        assert mock.attr2() == "returning 2"

    def test_flexmock_should_accept_shortcuts_for_creating_expectations(self):
        class Foo:
            def method1(self):
                pass

            def method2(self):
                pass

        instance = Foo()
        flexmock(instance, method1="returning 1", method2="returning 2")
        assert instance.method1() == "returning 1"
        assert instance.method2() == "returning 2"
        assert instance.method2() == "returning 2"

    def test_flexmock_expectations_returns_all(self):
        mock = flexmock(name="temp")
        assert mock not in FlexmockContainer.flexmock_objects
        mock.should_receive("method_foo")
        mock.should_receive("method_bar")
        assert len(FlexmockContainer.flexmock_objects[mock]) == 2

    def test_flexmock_expectations_returns_named_expectation(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._name == "method_foo"

    def test_flexmock_expectations_returns_none_if_not_found(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo")
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_bar") is None

    def test_flexmock_should_check_parameters(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("bar").and_return(1)
        mock.should_receive("method_foo").with_args("baz").and_return(2)
        assert mock.method_foo("bar") == 1
        assert mock.method_foo("baz") == 2

    def test_flexmock_should_keep_track_of_calls(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("foo").and_return(0)
        mock.should_receive("method_foo").with_args("bar").and_return(1)
        mock.should_receive("method_foo").with_args("baz").and_return(2)
        mock.method_foo("bar")
        mock.method_foo("bar")
        mock.method_foo("baz")
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("foo",))
        assert expectation._times_called == 0
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("bar",))
        assert expectation._times_called == 2
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("baz",))
        assert expectation._times_called == 1

    def test_flexmock_should_set_expectation_call_numbers(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").times(1)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called exactly 1 time, called 0 times",
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
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called == 1

    def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException(1, arg2=2))
        with assert_raises(FakeException, "1"):
            mock.method_foo()
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called == 1

    def test_flexmock_should_check_raised_exceptions_class_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException, 1, arg2=2)
        with assert_raises(FakeException, "1"):
            mock.method_foo()
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo")._times_called == 1

    def test_flexmock_should_match_any_args_by_default(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar")
        mock.should_receive("method_foo").with_args("baz").and_return("baz")
        assert mock.method_foo() == "bar"
        assert mock.method_foo(1) == "bar"
        assert mock.method_foo("foo", "bar") == "bar"
        assert mock.method_foo("baz") == "baz"

    def test_flexmock_should_fail_to_match_exactly_no_args_when_calling_with_args(self):
        mock = flexmock()
        mock.should_receive("method_foo").with_args()
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method_foo did not match expectations:\n"
                '  Received call:\tmethod_foo("baz")\n'
                "  Expected call[1]:\tmethod_foo()"
            ),
        ):
            mock.method_foo("baz")

    def test_flexmock_should_match_exactly_no_args(self):
        class Foo:
            def method(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args().and_return("baz")
        assert instance.method() == "baz"

    def test_expectation_dot_mock_should_return_mock(self):
        mock = flexmock(name="temp")
        assert mock.should_receive("method_foo").mock() == mock

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
        assert user.get_name() == "john"

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
        assert user.get_name() == "john"

    def test_flexmock_should_create_partial_new_style_class_mock(self):
        class User:
            def __init__(self):
                pass

            def get_name(self):
                pass

        flexmock(User)
        User.should_receive("get_name").and_return("mike")
        user = User()
        assert user.get_name() == "mike"

    def test_flexmock_should_create_partial_old_style_class_mock(self):
        class User:
            def __init__(self):
                pass

            def get_name(self):
                pass

        flexmock(User)
        User.should_receive("get_name").and_return("mike")
        user = User()
        assert user.get_name() == "mike"

    def test_flexmock_should_match_expectations_against_builtin_classes(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args(str).and_return("got a string")
        mock.should_receive("method_foo").with_args(int).and_return("got an int")
        assert mock.method_foo("string!") == "got a string"
        assert mock.method_foo(23) == "got an int"
        with assert_raises(
            exceptions.MethodSignatureError,
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
        flexmock_teardown()
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
        assert mock.method_foo(Foo()) == "got a Foo"
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method_foo did not match expectations:\n"
                "  Received call:\tmethod_foo(1)\n"
                "  Expected call[1]:\tmethod_foo(<class 'tests.features.mocking.MockingTestCase"
                ".test_flexmock_should_match_expectations_against_user_defined_classes"
                ".<locals>.Foo'>)"
            ),
        ):
            mock.method_foo(1)

    def test_flexmock_configures_global_mocks_dict(self):
        mock = flexmock(name="temp")
        assert mock not in FlexmockContainer.flexmock_objects
        mock.should_receive("method_foo")
        assert mock in FlexmockContainer.flexmock_objects
        assert len(FlexmockContainer.flexmock_objects[mock]) == 1

    def test_flexmock_teardown_verifies_mocks(self):
        mock = flexmock(name="temp")
        mock.should_receive("verify_expectations").times(1)
        with assert_raises(
            exceptions.MethodCallError,
            "verify_expectations() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()

    def test_flexmock_teardown_does_not_verify_stubs(self):
        mock = flexmock(name="temp")
        mock.should_receive("verify_expectations")
        flexmock_teardown()

    def test_flexmock_preserves_stubbed_object_methods_between_tests(self):
        class User:
            def get_name(self):
                return "mike"

        user = User()
        flexmock(user).should_receive("get_name").and_return("john")
        assert user.get_name() == "john"
        flexmock_teardown()
        assert user.get_name() == "mike"

    def test_flexmock_preserves_stubbed_class_methods_between_tests(self):
        class User:
            def get_name(self):
                return "mike"

        user = User()
        flexmock(User).should_receive("get_name").and_return("john")
        assert user.get_name() == "john"
        flexmock_teardown()
        assert user.get_name() == "mike"

    def test_flexmock_removes_new_stubs_from_objects_after_tests(self):
        class User:
            def get_name(self):
                pass

        user = User()
        saved = user.get_name
        flexmock(user).should_receive("get_name").and_return("john")
        assert saved != user.get_name
        assert user.get_name() == "john"
        flexmock_teardown()
        assert user.get_name == saved

    def test_flexmock_removes_new_stubs_from_classes_after_tests(self):
        class User:
            def get_name(self):
                pass

        user = User()
        saved = user.get_name
        flexmock(User).should_receive("get_name").and_return("john")
        assert saved != user.get_name
        assert user.get_name() == "john"
        flexmock_teardown()
        assert user.get_name == saved

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
        assert user.get_name() == "john"
        assert group.get_name() == "john"
        flexmock_teardown()
        assert user.get_name == saved1
        assert group.get_name == saved2

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
        assert user.get_name() == "john"
        assert group.get_name() == "john"
        flexmock_teardown()
        assert user.get_name == saved1
        assert group.get_name == saved2

    def test_flexmock_stubs_are_callable(self):
        stub = flexmock()
        mocked = flexmock()
        mocked.should_receive("create").twice()
        stub.tickets = mocked
        # stub.tickets should work with and without parentheses
        stub.tickets().create()
        stub.tickets.create()
        flexmock_teardown()

    def test_flexmock_respects_at_least_when_called_less_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar").at_least().twice()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_LEAST
        mock.method_foo()
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called at least 2 times, called 1 time",
        ):
            flexmock_teardown()

    def test_flexmock_respects_at_least_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_LEAST
        mock.method_foo()
        flexmock_teardown()

    def test_flexmock_respects_at_least_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_LEAST
        mock.method_foo()
        mock.method_foo()
        flexmock_teardown()

    def test_flexmock_respects_at_most_when_called_less_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar").at_most().twice()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_MOST
        mock.method_foo()
        flexmock_teardown()

    def test_flexmock_respects_at_most_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_MOST
        mock.method_foo()
        flexmock_teardown()

    def test_flexmock_respects_at_most_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._modifier == AT_MOST
        mock.method_foo()
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called at most 1 time, called 2 times",
        ):
            mock.method_foo()

    def test_flexmock_treats_once_as_times_one(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._expected_calls[EXACTLY] == 1
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()

    def test_flexmock_treats_twice_as_times_two(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").twice().and_return("value_bar")
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._expected_calls[EXACTLY] == 2
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called exactly 2 times, called 0 times",
        ):
            flexmock_teardown()

    def test_flexmock_works_with_never_when_true(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert expectation._expected_calls[EXACTLY] == 0
        flexmock_teardown()

    def test_flexmock_works_with_never_when_false(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        with assert_raises(
            exceptions.MethodCallError,
            "method_foo() expected to be called exactly 0 times, called 1 time",
        ):
            mock.method_foo()

    def test_flexmock_get_flexmock_expectation_should_work_with_args(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").with_args("value_bar")
        assert FlexmockContainer.get_flexmock_expectation(mock, "method_foo", "value_bar")

    def test_mock_kwargs_only_func_mock_all(self):
        flexmock(some_module).should_receive("kwargs_only_func1").with_args(
            1, bar=2, baz=3
        ).and_return(123)
        assert some_module.kwargs_only_func1(1, bar=2, baz=3) == 123

    def test_mock_kwargs_only_func_mock_required(self):
        flexmock(some_module).should_receive("kwargs_only_func1").with_args(1, bar=2).and_return(
            123
        )
        assert some_module.kwargs_only_func1(1, bar=2) == 123

    def test_mock_kwargs_only_func_fails_if_required_not_provided(self):
        with assert_raises(
            exceptions.MethodSignatureError,
            'kwargs_only_func1 requires keyword-only argument "bar"',
        ):
            flexmock(some_module).should_receive("kwargs_only_func1").with_args(1)
        with assert_raises(
            exceptions.MethodSignatureError,
            'kwargs_only_func2 requires keyword-only arguments "bar", "baz"',
        ):
            flexmock(some_module).should_receive("kwargs_only_func2").with_args(2)

    def test_context_manager_on_instance(self):
        class CM:
            def __enter__(self):
                pass

            def __exit__(self, *_):
                pass

        instance = CM()
        flexmock(instance).should_call("__enter__").once()
        flexmock(instance).should_call("__exit__").once()
        with instance:
            pass
        flexmock_teardown()

    def test_context_manager_on_class(self):
        class CM:
            def __enter__(self):
                pass

            def __exit__(self, *_):
                pass

        instance = CM()
        flexmock(CM).should_receive("__enter__").once()
        flexmock(CM).should_receive("__exit__").once()
        with instance:
            pass
        flexmock_teardown()

    def test_flexmock_should_support_with(self):
        mocked = flexmock()
        with mocked as mock:
            mock.should_receive("bar").and_return("baz")
        assert mocked.bar() == "baz"

    def test_builtin_open(self):
        mock = flexmock(sys.modules["builtins"])
        fake_fd = flexmock(read=lambda: "some data")
        mock.should_receive("open").once().with_args("file_name").and_return(fake_fd)
        with open("file_name") as file:  # pylint: disable=unspecified-encoding
            data = file.read()
        assert data == "some data"

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
        assert mocked.prop1 == "mocked1"
        assert mocked.prop2 == "mocked2"

    def test_mock_property_with_attribute_on_instance(self):
        class Foo:
            @property
            def method(self):
                return "bar"

        foo1 = Foo()
        foo2 = Foo()
        foo3 = Foo()
        flexmock(foo1, method="baz")
        flexmock(foo2, method="baz2")
        assert foo1.method == "baz"
        assert foo2.method == "baz2"
        assert foo3.method == "bar"
        flexmock_teardown()
        assert hasattr(Foo, "_flexmock__method") is False, "Property method not cleaned up"
        assert foo1.method == "bar"
        assert foo2.method == "bar"
        assert foo3.method == "bar"

    def test_mock_property_with_attribute_on_class(self):
        class Foo:
            @property
            def method(self):
                return "bar"

        foo1 = Foo()
        foo2 = Foo()
        flexmock(Foo, method="baz")
        assert foo1.method == "baz"
        assert foo2.method == "baz"
        flexmock_teardown()
        assert hasattr(Foo, "_flexmock__method") is False, "Property method not cleaned up"
        assert foo1.method == "bar"
        assert foo2.method == "bar"

    def test_verifying_methods_when_mocking_module(self):
        # previously, we had problems with recognizing methods vs functions if the mocked
        # object was an imported module
        flexmock(some_module).should_receive("ModuleClass").with_args(1, 2)
        flexmock(some_module).should_receive("module_function").with_args(1, 2)

    def test_fake_object_supporting_iteration(self):
        mocked = flexmock()
        mocked.should_receive("__iter__").and_yield(1, 2, 3)
        assert list(mocked) == [1, 2, 3]

    def test_with_args_for_single_named_arg_with_optional_args(self):
        class FooClass:
            def method(self, one, two="optional"):
                pass

        flexmock(FooClass).should_receive("method").with_args(one=1)

    def test_with_args_doesnt_set_max_when_using_varargs(self):
        class FooClass:
            def method(self, *args):
                pass

        flexmock(FooClass).should_receive("method").with_args(1, 2, 3)

    def test_with_args_doesnt_set_max_when_using_kwargs(self):
        class FooClass:
            def method(self, **kwargs):
                pass

        flexmock(FooClass).should_receive("method").with_args(1, 2, 3)

    def test_with_args_blows_up_on_too_few_args(self):
        class FooClass:
            def method1(self, arg1):
                pass

            def method2(self, arg1, arg2, arg3=1):
                pass

        mock = flexmock(FooClass)
        expectation1 = mock.should_receive("method1")
        expectation2 = mock.should_receive("method2")
        with assert_raises(
            exceptions.MethodSignatureError,
            "method1 requires at least 1 argument, expectation provided 0",
        ):
            expectation1.with_args()
        with assert_raises(
            exceptions.MethodSignatureError,
            "method2 requires at least 2 arguments, expectation provided 1",
        ):
            expectation2.with_args(1)

    def test_with_args_blows_up_on_too_few_args_with_kwargs(self):
        class FooClass:
            def method(self, arg1, arg2, arg3=1):
                pass

        expectation = flexmock(FooClass).should_receive("method")
        with assert_raises(
            exceptions.MethodSignatureError,
            "method requires at least 3 arguments, expectation provided 2",
        ):
            expectation.with_args(1, arg3=2)

    def test_with_args_blows_up_on_too_many_args(self):
        class FooClass:
            def method(self, arg1, arg2, arg3=1):
                pass

        expectation = flexmock(FooClass).should_receive("method")
        with assert_raises(
            exceptions.MethodSignatureError,
            "method requires at most 3 arguments, expectation provided 4",
        ):
            expectation.with_args(1, 2, 3, 4)

    def test_with_args_blows_up_on_kwarg_overlapping_positional(self):
        class FooClass:
            def method(self, arg1, arg2, arg3=1, **kwargs):
                pass

        expectation = flexmock(FooClass).should_receive("method")
        with assert_raises(
            exceptions.MethodSignatureError,
            "['arg3'] already given as positional argument to method",
        ):
            expectation.with_args(1, 2, 3, arg3=2)
        with assert_raises(
            exceptions.MethodSignatureError,
            "['arg3', 'arg2'] already given as positional arguments to method",
        ):
            expectation.with_args(1, 2, 3, arg3=2, arg2=3)

    def test_with_args_blows_up_on_invalid_kwarg(self):
        class FooClass:
            def method(self, arg1, arg2, arg3=1):
                pass

        with assert_raises(
            exceptions.MethodSignatureError, "d is not a valid keyword argument to method"
        ):
            flexmock(FooClass).should_receive("method").with_args(1, 2, d=2)

    def test_with_args_ignores_invalid_args_on_flexmock_instances(self):
        instance = flexmock(bar=lambda x: x)
        instance.should_receive("bar").with_args("stuff")
        instance.bar("stuff")

    def test_with_args_does_not_compensate_for_self_on_static_instance_methods(self):
        class FooClass:
            @staticmethod
            def method(arg):
                pass

        instance = FooClass()
        flexmock(instance).should_receive("method").with_args("stuff")
        instance.method("stuff")

    def test_with_args_does_not_compensate_for_self_on_static_class_methods(self):
        class FooClass:
            @staticmethod
            def method(arg):
                pass

        flexmock(FooClass).should_receive("method").with_args("stuff")
        FooClass.method("stuff")

    def test_with_args_does_compensate_for_cls_on_class_methods(self):
        class FooClass:
            @classmethod
            def method(cls, arg):
                pass

        instance = FooClass()
        flexmock(instance).should_receive("method").with_args("stuff")
        instance.method("stuff")

    def test_calling_with_keyword_args_matches_mock_with_positional_args(self):
        class FooClass:
            def method(self, arg1, arg2, arg3):
                pass

        instance = FooClass()
        flexmock(instance).should_receive("method").with_args(1, 2, 3).once()
        instance.method(arg1=1, arg2=2, arg3=3)

    def test_calling_with_positional_args_matches_mock_with_kwargs(self):
        class FooClass:
            def method(self, arg1, arg2, arg3):
                pass

        instance = FooClass()
        flexmock(instance).should_receive("method").with_args(arg1=1, arg2=2, arg3=3).once()
        instance.method(1, 2, arg3=3)

    def test_and_return_defaults_to_none_with_no_arguments(self):
        mocked = flexmock()
        mocked.should_receive("bar").and_return()
        assert mocked.bar() is None

    def test_non_callable_attributes_fail_to_set_expectations(self):
        class FooClass:
            attribute = 1

        instance = FooClass()
        expectation = flexmock(instance).should_receive("attribute").and_return(2)
        with assert_raises(exceptions.FlexmockError, "can't use times() with attribute stubs"):
            expectation.times(1)
        with assert_raises(exceptions.FlexmockError, "can't use with_args() with attribute stubs"):
            expectation.with_args(())
        with assert_raises(
            exceptions.FlexmockError, "can't use replace_with() with attribute/property stubs"
        ):
            expectation.replace_with(lambda x: x)
        with assert_raises(exceptions.FlexmockError, "can't use and_raise() with attribute stubs"):
            expectation.and_raise(Exception)
        with assert_raises(exceptions.FlexmockError, "can't use when() with attribute stubs"):
            expectation.when(lambda x: x)
        with assert_raises(exceptions.FlexmockError, "can't use and_yield() with attribute stubs"):
            expectation.and_yield(1)
        with assert_raises(exceptions.FlexmockError, "can't use ordered() with attribute stubs"):
            object.__getattribute__(expectation, "ordered")()
        with assert_raises(exceptions.FlexmockError, "can't use at_least() with attribute stubs"):
            object.__getattribute__(expectation, "at_least")()
        with assert_raises(exceptions.FlexmockError, "can't use at_most() with attribute stubs"):
            object.__getattribute__(expectation, "at_most")()
        with assert_raises(exceptions.FlexmockError, "can't use one_by_one() with attribute stubs"):
            object.__getattribute__(expectation, "one_by_one")()

    def test_should_chain_attributes(self):
        class Class1:
            x = 1

        class Class2:
            class1 = Class1()

        class Class3:
            class2 = Class2()

        class3 = Class3()
        mocked = flexmock(class3)
        mocked.should_receive("class2.class1.x").and_return(2)
        assert mocked.class2.class1.x == 2
        flexmock_teardown()
        assert mocked.class2.class1.x == 1

    def test_mocking_subclass_of_str(self):
        class String(str):
            pass

        string = String()
        flexmock(string, endswith="fake")
        assert string.endswith("stuff") == "fake"
        flexmock_teardown()
        assert string.endswith("stuff") is False

    def test_proper_reset_of_subclass_methods(self):
        class ClassA:
            def method(self):
                return "a"

        class ClassB(ClassA):
            def method(self):
                return "b"

        flexmock(ClassB).should_receive("method").and_return("1")
        flexmock_teardown()
        assert ClassB().method() == "b"

    def test_flexmock_class_returns_same_object_on_repeated_calls(self):
        class Foo:
            pass

        first = flexmock(Foo)
        second = flexmock(Foo)
        assert first is second

    def test_flexmock_object_returns_same_object_on_repeated_calls(self):
        class Foo:
            pass

        instance = Foo()
        first = flexmock(instance)
        second = flexmock(instance)
        assert first is second

    def test_mocking_down_the_inheritance_chain_class_to_class(self):
        class Parent:
            def method1(self):
                pass

        class Child(Parent):
            def method2(self):
                pass

        flexmock(Parent).should_receive("method1").and_return("outer")
        flexmock(Child).should_receive("method2").and_return("inner")
        assert Parent().method1() == "outer"
        assert Child().method2() == "inner"

    def test_flexmock_should_mock_the_same_method_multiple_times(self):
        class Foo:
            def method(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").and_return(1)
        assert instance.method() == 1
        flexmock(instance).should_receive("method").and_return(2)
        assert instance.method() == 2
        flexmock(instance).should_receive("method").and_return(3)
        assert instance.method() == 3
        flexmock(instance).should_receive("method").and_return(4)
        assert instance.method() == 4

    def test_new_instances_should_be_a_method(self):
        class Foo:
            pass

        flexmock(Foo).new_instances("bar")
        assert Foo() == "bar"
        flexmock_teardown()
        assert Foo() != "bar"

    def test_new_instances_raises_error_when_not_a_class(self):
        class Foo:
            pass

        instance = Foo()
        flexmock(instance)
        with assert_raises(
            exceptions.FlexmockError, "new_instances can only be called on a class mock"
        ):
            instance.new_instances("bar")

    def test_new_instances_works_with_multiple_return_values(self):
        class Foo:
            pass

        flexmock(Foo).new_instances("foo", "bar")
        assert Foo() == "foo"
        assert Foo() == "bar"

    def test_should_receive_should_not_replace_flexmock_methods(self):
        class Foo:
            pass

        instance = Foo()
        flexmock(instance)
        for method_name in ["should_receive", "should_call", "new_instances"]:
            with assert_raises(exceptions.FlexmockError, "unable to replace flexmock methods"):
                instance.should_receive(method_name)

    def test_flexmock_should_not_add_methods_if_they_already_exist(self):
        class Foo:
            def should_receive(self):
                return "real"

            def method(self):
                pass

        instance = Foo()
        mock = flexmock(instance)
        assert instance.should_receive() == "real"
        assert "should_call" not in dir(instance)
        assert "new_instances" not in dir(instance)
        mock.should_receive("method").and_return("baz")
        assert instance.method() == "baz"
        flexmock_teardown()
        assert instance.should_receive() == "real"

    def test_flexmock_should_not_add_class_methods_if_they_already_exist(self):
        class Foo:
            def should_receive(self):
                return "real"

            def method(self):
                pass

        instance = Foo()
        mock = flexmock(Foo)
        assert instance.should_receive() == "real"
        assert "should_call" not in dir(Foo)
        assert "new_instances" not in dir(Foo)
        mock.should_receive("method").and_return("baz")
        assert instance.method() == "baz"
        flexmock_teardown()
        assert instance.should_receive() == "real"

    def test_flexmock_should_replace_method(self):
        class Foo:
            def method(self, arg):
                return arg

        instance = Foo()
        flexmock(instance).should_receive("method").replace_with(lambda x: x == 5)
        assert instance.method(5) is True
        assert instance.method(4) is False

    def test_flexmock_should_replace_cannot_be_specified_twice(self):
        class Foo:
            def method(self, arg):
                return arg

        instance = Foo()
        expectation = flexmock(instance).should_receive("method").replace_with(lambda x: x == 5)
        with assert_raises(exceptions.FlexmockError, "replace_with cannot be specified twice"):
            expectation.replace_with(lambda x: x == 3)

    def test_should_give_reasonable_error_for_builtins(self):
        with assert_raises(
            exceptions.MockBuiltinError,
            (
                "Python does not allow you to mock builtin objects or modules. "
                "Consider wrapping it in a class you can mock instead"
            ),
        ):
            flexmock(object)

    def test_should_give_reasonable_error_for_instances_of_builtins(self):
        with assert_raises(
            exceptions.MockBuiltinError,
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

        instance = Bar()
        assert instance.method1().method2() == "foo"
        flexmock(instance).should_receive("method1.method2").and_return("bar")
        assert instance.method1().method2() == "bar"

    def test_mock_chained_method_supports_args_and_mocks(self):
        class Foo:
            def method2(self, arg):
                return arg

        class Bar:
            def method1(self):
                return Foo()

        instance = Bar()
        assert instance.method1().method2("foo") == "foo"
        flexmock(instance).should_receive("method1.method2").with_args("foo").and_return(
            "bar"
        ).once()
        assert instance.method1().method2("foo") == "bar"
        flexmock_teardown()
        flexmock(instance).should_receive("method1.method2").with_args("foo").and_return(
            "bar"
        ).once()
        with assert_raises(
            exceptions.MethodCallError,
            'method2("foo") expected to be called exactly 1 time, called 0 times',
        ):
            flexmock_teardown()

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

        instance = Bar()
        assert instance.method1().method2().method3() == "foo"
        flexmock(instance).should_receive("method1.method2.method3").and_return("bar")
        assert instance.method1().method2().method3() == "bar"

    def test_flexmock_should_fail_mocking_nonexistent_methods(self):
        class User:
            pass

        user = User()
        with assert_raises(
            exceptions.FlexmockError,
            re.compile(
                r"<.+\.<locals>\.User object at 0x.+> does not have attribute 'nonexistent'"
            ),
        ):
            flexmock(user).should_receive("nonexistent")

    def test_new_instances_should_blow_up_on_should_receive(self):
        class User:
            pass

        mock = flexmock(User).new_instances(None).mock()
        with assert_raises(exceptions.FlexmockError, "User does not have attribute 'foo'"):
            mock.should_receive("foo")

    def test_flexmock_should_support_mocking_classes_as_functions(self):
        flexmock(some_module).should_receive("SomeClass").and_return("yay")
        assert some_module.SomeClass() == "yay"

    def test_flexmock_should_properly_restore_class_methods(self):
        class User:
            @classmethod
            def get_stuff(cls):
                return cls.__name__

        assert isinstance(User.__dict__["get_stuff"], classmethod)
        assert User.get_stuff() == "User"
        flexmock(User).should_receive("get_stuff").and_return("foo")
        assert User.get_stuff() == "foo"
        flexmock_teardown()
        assert User.get_stuff() == "User"
        assert isinstance(User.__dict__["get_stuff"], classmethod)

    def test_flexmock_should_mock_same_class_twice(self):
        class Foo:
            pass

        flexmock(Foo)
        flexmock(Foo)

    def test_and_raise_with_invalid_arguments(self):
        with assert_raises(
            exceptions.FlexmockError,
            "can't initialize <class 'Exception'> with the given arguments",
        ):
            flexmock().should_receive("foo").and_raise(Exception, 1, bar=2)

    def test_flexmock_should_mock_iter_on_new_style_instances(self):
        class Foo:
            def __iter__(self):
                yield None

        old = Foo.__iter__
        foo1 = Foo()
        foo2 = Foo()
        foo3 = Foo()
        flexmock(foo1, __iter__=iter([1, 2, 3]))
        flexmock(foo2, __iter__=iter([3, 4, 5]))
        assert list(foo1) == [1, 2, 3]
        assert list(foo2) == [3, 4, 5]
        assert list(foo3) == [None]
        assert foo1.__iter__ is not old
        assert foo2.__iter__ is not old
        assert foo3.__iter__ is not old
        flexmock_teardown()
        assert list(foo1) == [None]
        assert list(foo2) == [None]
        assert list(foo3) == [None]
        assert Foo.__iter__ is old, f"{Foo.__iter__} != {old}"

    def test_flexmock_should_mock_private_methods_with_leading_underscores(self):
        class ClassWithPrivateMethods:
            def __private_instance_method(self):
                pass

            @classmethod
            def __private_class_method(cls):
                pass

            def instance_method(self):
                return self.__private_instance_method()

            @classmethod
            def class_method(cls):
                return cls.__private_class_method()

        # Instance
        instance = ClassWithPrivateMethods()
        flexmock(instance).should_receive("__private_instance_method").and_return("bar")
        assert instance.instance_method() == "bar"

        # Class
        flexmock(ClassWithPrivateMethods).should_receive("__private_class_method").and_return("baz")
        assert ClassWithPrivateMethods.class_method() == "baz"

    def test_flexmock_should_mock_generators(self):
        class Gen:
            def method(self):
                pass

        gen = Gen()
        flexmock(gen).should_receive("method").and_yield(*range(1, 10))
        output = list(gen.method())
        assert list(range(1, 10)) == output

    def test_flexmock_should_mock_private_methods(self):
        class Foo:
            def __private_method(self):
                return "foo"

            def public_method(self):
                return self.__private_method()

        instance = Foo()
        flexmock(instance).should_receive("__private_method").and_return("bar")
        assert instance.public_method() == "bar"

    def test_flexmock_should_mock_special_methods(self):
        class Foo:
            def __special_method__(self):
                return "foo"

            def public_method(self):
                return self.__special_method__()

        instance = Foo()
        flexmock(instance).should_receive("__special_method__").and_return("bar")
        assert instance.public_method() == "bar"

    def test_flexmock_should_mock_double_underscore_method(self):
        class Foo:
            def __(self):
                return "foo"

            def public_method(self):
                return self.__()

        instance = Foo()
        flexmock(instance).should_receive("__").and_return("bar")
        assert instance.public_method() == "bar"

    def test_flexmock_should_mock_private_class_methods(self):
        class Foo:
            def __iter__(self):
                pass

        flexmock(Foo).should_receive("__iter__").and_yield(1, 2, 3)
        assert list(Foo()) == [1, 2, 3]

    def test_flexmock_doesnt_error_on_properly_ordered_expectations(self):
        class Foo:
            def method1(self):
                pass

            def method2(self, arg1):
                pass

            def method3(self):
                pass

            def method4(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method1")
        flexmock(instance).should_receive("method2").with_args("a").ordered()
        flexmock(instance).should_receive("method3")
        flexmock(instance).should_receive("method2").with_args("b").ordered()
        flexmock(instance).should_receive("method4")
        instance.method3()
        instance.method2("a")
        instance.method2("b")
        instance.method4()
        instance.method1()

    def test_flexmock_errors_on_improperly_ordered_expectations(self):
        class Foo:
            def method1(self, arg1):
                pass

        instance = Foo()
        flexmock(instance)
        instance.should_receive("method1").with_args("a").ordered()
        instance.should_receive("method1").with_args("b").ordered()
        with assert_raises(
            exceptions.CallOrderError, 'method1("b") called before method1(arg1="a")'
        ):
            instance.method1("b")

    def test_flexmock_should_accept_multiple_return_values(self):
        class Foo:
            def method1(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method1").and_return(1, 5).and_return(2)
        assert instance.method1() == (1, 5)
        assert instance.method1() == 2
        assert instance.method1() == (1, 5)
        assert instance.method1() == 2

    def test_flexmock_should_accept_multiple_return_values_with_shortcut(self):
        class Foo:
            def method1(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method1").and_return(1, 2).one_by_one()
        assert instance.method1() == 1
        assert instance.method1() == 2
        assert instance.method1() == 1
        assert instance.method1() == 2

    def test_flexmock_should_accept_multiple_return_values_with_one_by_one(self):
        mocked = flexmock()
        flexmock(mocked).should_receive("method1").and_return(2).and_return(3).one_by_one()
        assert mocked.method1() == 2
        assert mocked.method1() == 3
        assert mocked.method1() == 2
        assert mocked.method1() == 3

    def test_one_by_one_called_before_and_return_multiple_values(self):
        mocked = flexmock()
        mocked.should_receive("method1").one_by_one().and_return(3, 4)
        assert mocked.method1() == 3
        assert mocked.method1() == 4
        assert mocked.method1() == 3
        assert mocked.method1() == 4

    def test_one_by_one_called_before_and_return_one_value(self):
        mocked = flexmock()
        mocked.should_receive("method1").one_by_one().and_return(4).and_return(5)
        assert mocked.method1() == 4
        assert mocked.method1() == 5
        assert mocked.method1() == 4
        assert mocked.method1() == 5

    def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
        class Foo:
            def method1(self):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method1").and_return(1).and_raise(Exception)
        assert instance.method1() == 1
        with assert_raises(Exception, ""):
            instance.method1()
        assert instance.method1() == 1
        with assert_raises(Exception, ""):
            instance.method1()

    def test_flexmock_should_mock_new_instances_with_multiple_params(self):
        class User:
            pass

        class Group:
            def __init__(self, arg, arg2):
                pass

        user = User()
        flexmock(Group).new_instances(user)
        assert user is Group(1, 2)

    def test_flexmock_function_should_return_previously_mocked_object(self):
        class User:
            pass

        user = User()
        instance = flexmock(user)
        assert instance == user
        assert instance == flexmock(user)

    def test_flexmock_should_not_return_class_object_if_mocking_instance(self):
        class User:
            def method(self):
                pass

        user = User()
        user2 = User()
        class_mock = flexmock(User).should_receive("method").and_return("class").mock()
        user_mock = flexmock(user).should_receive("method").and_return("instance").mock()
        assert class_mock is not user_mock
        assert user.method() == "instance"
        assert user2.method() == "class"
