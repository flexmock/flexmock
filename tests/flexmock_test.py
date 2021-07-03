"""Flexmock tests."""
# pylint: disable=missing-docstring,too-many-lines,broad-except,disallowed-name,no-member,invalid-name,no-self-use
import re
import sys
import unittest

from flexmock import (
    AT_LEAST,
    AT_MOST,
    EXACTLY,
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
    _isproperty,
    flexmock,
    flexmock_teardown,
)
from tests import some_module


def module_level_function(some, args):
    return "%s, %s" % (some, args)


MODULE_LEVEL_ATTRIBUTE = "test"


class OldStyleClass:
    pass


class NewStyleClass:
    pass


def assert_raises(exception, method, *kargs, **kwargs):
    try:
        method(*kargs, **kwargs)
    except exception:
        return
    except Exception:
        instance = sys.exc_info()[1]
        print("%s" % instance)
    raise Exception("%s not raised" % exception.__name__)


def assert_equal(expected, received, msg=""):
    if not msg:
        msg = "expected %s, received %s" % (expected, received)
    if expected != received:
        raise AssertionError("%s != %s : %s" % (expected, received, msg))


class RegularClass:
    def _tear_down(self):
        return flexmock_teardown()

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
        assert "method_foo" in [x.name for x in FlexmockContainer.flexmock_objects[mock]]

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

        flexmock(Foo).should_receive(u"bar").and_return("mocked_bar")

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
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo").name,
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
        assert_equal(0, expectation.times_called)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("bar",))
        assert_equal(2, expectation.times_called)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo", ("baz",))
        assert_equal(1, expectation.times_called)

    def test_flexmock_should_set_expectation_call_numbers(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").times(1)
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_raises(MethodCallError, expectation.verify)
        mock.method_foo()
        expectation.verify()

    def test_flexmock_should_check_raised_exceptions(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            pass

        mock.should_receive("method_foo").and_raise(FakeException)
        assert_raises(FakeException, mock.method_foo)
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo").times_called,
        )

    def test_flexmock_should_check_raised_exceptions_instance_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException(1, arg2=2))
        assert_raises(FakeException, mock.method_foo)
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo").times_called,
        )

    def test_flexmock_should_check_raised_exceptions_class_with_args(self):
        mock = flexmock(name="temp")

        class FakeException(Exception):
            def __init__(self, arg, arg2):
                # pylint: disable=super-init-not-called
                pass

        mock.should_receive("method_foo").and_raise(FakeException, 1, arg2=2)
        assert_raises(FakeException, mock.method_foo)
        assert_equal(
            1,
            FlexmockContainer.get_flexmock_expectation(mock, "method_foo").times_called,
        )

    def test_flexmock_should_match_any_args_by_default(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar")
        mock.should_receive("method_foo").with_args("baz").and_return("baz")
        assert_equal("bar", mock.method_foo())
        assert_equal("bar", mock.method_foo(1))
        assert_equal("bar", mock.method_foo("foo", "bar"))
        assert_equal("baz", mock.method_foo("baz"))

    def test_flexmock_should_fail_to_match_exactly_no_args_when_calling_with_args(self):
        mock = flexmock()
        mock.should_receive("method_foo").with_args()
        assert_raises(MethodSignatureError, mock.method_foo, "baz")

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
        assert_raises(MethodSignatureError, mock.method_foo, 2.0)

    def test_flexmock_should_match_expectations_against_user_defined_classes(self):
        mock = flexmock(name="temp")

        class Foo:
            pass

        mock.should_receive("method_foo").with_args(Foo).and_return("got a Foo")
        assert_equal("got a Foo", mock.method_foo(Foo()))
        assert_raises(MethodSignatureError, mock.method_foo, 1)

    def test_flexmock_configures_global_mocks_dict(self):
        mock = flexmock(name="temp")
        assert mock not in FlexmockContainer.flexmock_objects
        mock.should_receive("method_foo")
        assert mock in FlexmockContainer.flexmock_objects
        assert_equal(len(FlexmockContainer.flexmock_objects[mock]), 1)

    def test_flexmock_teardown_verifies_mocks(self):
        mock = flexmock(name="temp")
        mock.should_receive("verify_expectations").times(1)
        assert_raises(MethodCallError, self._tear_down)

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
        assert_equal(AT_LEAST, expectation.modifier)
        mock.method_foo()
        assert_raises(MethodCallError, self._tear_down)

    def test_flexmock_respects_at_least_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_LEAST, expectation.modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_least_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_least().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_LEAST, expectation.modifier)
        mock.method_foo()
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_less_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("bar").at_most().twice()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation.modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_requested_number(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation.modifier)
        mock.method_foo()
        self._tear_down()

    def test_flexmock_respects_at_most_when_called_more_than_requested(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").at_most().once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(AT_MOST, expectation.modifier)
        mock.method_foo()
        assert_raises(MethodCallError, mock.method_foo)

    def test_flexmock_treats_once_as_times_one(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").once()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(1, expectation.expected_calls[EXACTLY])
        assert_raises(MethodCallError, self._tear_down)

    def test_flexmock_treats_twice_as_times_two(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").twice().and_return("value_bar")
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(2, expectation.expected_calls[EXACTLY])
        assert_raises(MethodCallError, self._tear_down)

    def test_flexmock_works_with_never_when_true(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        expectation = FlexmockContainer.get_flexmock_expectation(mock, "method_foo")
        assert_equal(0, expectation.expected_calls[EXACTLY])
        self._tear_down()

    def test_flexmock_works_with_never_when_false(self):
        mock = flexmock(name="temp")
        mock.should_receive("method_foo").and_return("value_bar").never()
        assert_raises(MethodCallError, mock.method_foo)

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
        assert_raises(MethodCallError, self._tear_down)
        flexmock(User).should_call("foo").twice()
        assert_equal("class", user1.foo())
        assert_equal("class", user2.foo())

        # Access instance attributes
        flexmock(User).should_call("bar").once()
        assert_raises(MethodCallError, self._tear_down)
        flexmock(User).should_call("bar").twice()
        assert_equal("value", user1.bar())
        assert_equal("value", user2.bar())

        # Try resetting the expectation
        flexmock(User).should_call("bar").once()
        assert_equal("value", user1.bar())

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
        assert_raises(MethodCallError, self._tear_down)
        for method in UPDATED_ATTRS:
            assert method not in dir(Group)
        for method in UPDATED_ATTRS:
            assert method not in dir(User)

    def test_flexmock_should_call_respects_matched_expectations(self):
        class Group:
            def method1(self, arg1, arg2="b"):
                return "%s:%s" % (arg1, arg2)

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
                return "%s:%s" % (arg1, arg2)

            def method2(self, a):
                pass

        group = Group()
        flexmock(group).should_call("method1").at_least().once()
        assert_raises(MethodCallError, self._tear_down)
        flexmock(group)
        group.should_call("method2").with_args("a").once()
        group.should_receive("method2").with_args("not a")
        group.method2("not a")
        assert_raises(MethodCallError, self._tear_down)

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
        assert_raises(CallOrderError, foo.method1, "b")

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

    def test_flexmock_should_mix_multiple_return_values_with_exceptions(self):
        class Foo:
            def method1(self):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").and_return(1).and_raise(Exception)
        assert_equal(1, foo.method1())
        assert_raises(Exception, foo.method1)
        assert_equal(1, foo.method1())
        assert_raises(Exception, foo.method1)

    def test_flexmock_should_match_types_on_multiple_arguments(self):
        class Foo:
            def method1(self, a, b):
                pass

        foo = Foo()
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        assert_equal("ok", foo.method1("some string", 12))
        assert_raises(MethodSignatureError, foo.method1, 12, 32)
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        assert_raises(MethodSignatureError, foo.method1, 12, "some string")
        flexmock(foo).should_receive("method1").with_args(str, int).and_return("ok")
        assert_raises(MethodSignatureError, foo.method1, "string", 12, 14)

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
        assert_raises(MethodSignatureError, foo.method1, "string", 12)
        flexmock(foo).should_receive("method1").with_args(object, object, object).and_return("ok")
        assert_raises(MethodSignatureError, foo.method1, "string", 12, 13, 14)

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
        assert_raises(MethodSignatureError, foo.method1, bar, "some string")
        flexmock(foo).should_receive("method1").with_args(object, Bar).and_return("ok")
        assert_raises(MethodSignatureError, foo.method1, 12, "some string")

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
        assert_raises(MethodSignatureError, foo.method1, arg2=2, arg3=3)
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2)
        assert_raises(MethodSignatureError, foo.method1, 1, arg2=2, arg3=4)
        flexmock(foo).should_receive("method1").with_args(1, arg3=3, arg2=2)
        assert_raises(MethodSignatureError, foo.method1, 1)

    def test_flexmock_should_call_should_match_keyword_arguments(self):
        class Foo:
            def method1(self, arg1, arg2=None, arg3=None):
                return "%s%s%s" % (arg1, arg2, arg3)

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
        assert_equal([1, 2, 3], [x for x in Foo()])

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
        assert_equal([1, 2, 3], [x for x in foo])
        assert_equal([3, 4, 5], [x for x in foo2])
        assert_equal([None], [x for x in foo3])
        assert_equal(False, foo.__iter__ is old)
        assert_equal(False, foo2.__iter__ is old)
        assert_equal(False, foo3.__iter__ is old)
        self._tear_down()
        assert_equal([None], [x for x in foo])
        assert_equal([None], [x for x in foo2])
        assert_equal([None], [x for x in foo3])
        assert_equal(True, Foo.__iter__ == old, "%s != %s" % (Foo.__iter__, old))

    def test_flexmock_should_mock_private_methods_with_leading_underscores(self):
        class _Foo:
            def __stuff(self):
                pass

            def public_method(self):
                return self.__stuff()

        foo = _Foo()
        flexmock(foo).should_receive("__stuff").and_return("bar")
        assert_equal("bar", foo.public_method())

    def test_flexmock_should_mock_generators(self):
        class Gen:
            def foo(self):
                pass

        gen = Gen()
        flexmock(gen).should_receive("foo").and_yield(*range(1, 10))
        output = [val for val in gen.foo()]
        assert_equal([val for val in range(1, 10)], output)

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
                self.message = "%s, %s" % (param, param2)
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
                return "%s, %s" % (self.p1, self.p2)

        class User:
            def get_stuff(self):
                raise FakeException("1", "2")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FakeException, "2", "1")
        assert_raises(ExceptionMessageError, user.get_stuff)

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
        assert_raises(ExceptionMessageError, user.get_stuff)

    def test_flexmock_should_blow_up_on_wrong_spy_exception_type(self):
        class User:
            def get_stuff(self):
                raise CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(MethodCallError)
        assert_raises(ExceptionClassError, user.get_stuff)

    def test_flexmock_should_match_spy_exception_parent_type(self):
        class User:
            def get_stuff(self):
                raise CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FlexmockError)
        user.get_stuff()

    def test_flexmock_should_blow_up_on_wrong_spy_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

            def get_more_stuff(self):
                return "other", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return("other", "stuff")
        assert_raises(MethodSignatureError, user.get_stuff)
        flexmock(user).should_call("get_more_stuff").and_return()
        assert_raises(MethodSignatureError, user.get_more_stuff)

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

        assert_equal("ok!", User.get_stuff())
        flexmock(User).should_receive("get_stuff")
        assert User.get_stuff() is None
        self._tear_down()
        assert_equal("ok!", User.get_stuff())

    def test_flexmock_should_properly_restore_undecorated_static_methods(self):
        class User:
            def get_stuff():
                return "ok!"

            get_stuff = staticmethod(get_stuff)

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
        assert_raises(FlexmockError, module_level_function, 1, args="not expected")

    def test_flexmock_should_support_mocking_old_style_classes_as_functions(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod).should_receive("OldStyleClass").and_return("yay")
        assert_equal("yay", OldStyleClass())

    def test_flexmock_should_support_mocking_new_style_classes_as_functions(self):
        if "tests.flexmock_test" in sys.modules:
            mod = sys.modules["tests.flexmock_test"]
        else:
            mod = sys.modules["__main__"]
        flexmock(mod).should_receive("NewStyleClass").and_return("yay")
        assert_equal("yay", NewStyleClass())

    def test_flexmock_should_properly_restore_class_methods(self):
        class User:
            @classmethod
            def get_stuff(cls):
                return cls.__name__

        assert_equal("User", User.get_stuff())
        flexmock(User).should_receive("get_stuff").and_return("foo")
        assert_equal("foo", User.get_stuff())
        self._tear_down()
        assert_equal("User", User.get_stuff())

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
        assert_raises(FlexmockError, foo.foo)
        assert_raises(FlexmockError, foo.bar)
        assert_raises(FlexmockError, foo.baz)
        assert_raises(FlexmockError, foo.quux)

    def test_new_instances_should_blow_up_on_should_receive(self):
        class User:
            pass

        mock = flexmock(User).new_instances(None).mock
        assert_raises(FlexmockError, mock.should_receive, "foo")

    def test_should_call_alias_should_create_a_spy(self):
        class Foo:
            def get_stuff(self):
                return "yay"

        foo = Foo()
        flexmock(foo).should_call("get_stuff").and_return("yay").once()
        assert_raises(MethodCallError, self._tear_down)

    def test_flexmock_should_fail_mocking_nonexistent_methods(self):
        class User:
            pass

        user = User()
        assert_raises(FlexmockError, flexmock(user).should_receive, "nonexistent")

    def test_flexmock_should_not_explode_on_unicode_formatting(self):
        formatted = _format_args("method", {"kargs": (chr(0x86C7),), "kwargs": {}})
        assert_equal('method("蛇")', formatted)

    def test_return_value_should_not_explode_on_unicode_values(self):
        return_value = ReturnValue(chr(0x86C7))
        assert_equal('"蛇"', "%s" % return_value)
        return_value = ReturnValue((chr(0x86C7), chr(0x86C7)))
        assert_equal('("蛇", "蛇")', "%s" % return_value)

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
        assert_raises(MethodCallError, self._tear_down)

    def test_should_give_reasonable_error_for_builtins(self):
        assert_raises(MockBuiltinError, flexmock, object)

    def test_should_give_reasonable_error_for_instances_of_builtins(self):
        assert_raises(MockBuiltinError, flexmock, object())

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
        assert_raises(MethodCallError, self._tear_down)

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
        assert_raises(FlexmockError, expectation.replace_with, lambda x: x == 3)

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
        assert_raises(FlexmockError, foo.new_instances, "bar")

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
        assert_raises(FlexmockError, foo.should_receive, "should_receive")

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
        assert_raises(MethodSignatureError, foo.foo, "arg1somejunkasdfa", arg2="a")

    def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_kwarg(self):
        class Foo:
            def foo(self, arg1, arg2):
                pass

        foo = Foo()
        flexmock(foo).should_receive("foo").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("a")
        ).and_return("mocked")
        assert_raises(MethodSignatureError, foo.foo, "arg1somejunkasdf", arg2="b")

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
        assert_raises(CallOrderError, foo.bar, "b")

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
        radio.should_receive("select_channel").once().when(lambda: radio.is_on)
        radio.should_call("adjust_volume").once().with_args(5).when(lambda: radio.is_on)

        assert_raises(StateError, radio.select_channel)
        assert_raises(StateError, radio.adjust_volume, 5)
        radio.is_on = True
        radio.select_channel()
        radio.adjust_volume(5)

    def test_support_at_least_and_at_most_together(self):
        class Foo:
            def bar(self):
                pass

        foo = Foo()
        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        assert_raises(MethodCallError, self._tear_down)

        flexmock(foo).should_call("bar").at_least().once().at_most().twice()
        foo.bar()
        foo.bar()
        assert_raises(MethodCallError, foo.bar)

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
        try:
            expectation.at_least().at_least()
            raise Exception("should not be able to specify at_least twice")
        except FlexmockError:
            pass

    def test_at_most_cannot_be_used_twice(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        try:
            expectation.at_most().at_most()
            raise Exception("should not be able to specify at_most twice")
        except FlexmockError:
            pass

    def test_at_least_cannot_be_specified_until_at_most_is_set(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        try:
            expectation.at_least().at_most()
            raise Exception("should not be able to specify at_most if at_least unset")
        except FlexmockError:
            pass

    def test_at_most_cannot_be_specified_until_at_least_is_set(self):
        class Foo:
            def bar(self):
                pass

        expectation = flexmock(Foo).should_receive("bar")
        try:
            expectation.at_most().at_least()
            raise Exception("should not be able to specify at_least if at_most unset")
        except FlexmockError:
            pass

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
        assert_raises(CallOrderError, s.endswith, "c")

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
        assert_raises(FlexmockError, e.times, 1)
        assert_raises(FlexmockError, e.with_args, ())
        assert_raises(FlexmockError, e.replace_with, lambda x: x)
        assert_raises(FlexmockError, e.and_raise, Exception)
        assert_raises(FlexmockError, e.when, lambda x: x)
        assert_raises(FlexmockError, e.and_yield, 1)
        assert_raises(FlexmockError, object.__getattribute__(e, "ordered"))
        assert_raises(FlexmockError, object.__getattribute__(e, "at_least"))
        assert_raises(FlexmockError, object.__getattribute__(e, "at_most"))
        assert_raises(FlexmockError, object.__getattribute__(e, "one_by_one"))

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
        assert_equal([1, 2, 3], [i for i in foo])

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
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        assert_raises(MethodSignatureError, e.with_args, 1)

    def test_with_args_blows_up_on_too_few_args_with_kwargs(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        assert_raises(MethodSignatureError, e.with_args, 1, c=2)

    def test_with_args_blows_up_on_too_many_args(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        assert_raises(MethodSignatureError, e.with_args, 1, 2, 3, 4)

    def test_with_args_blows_up_on_kwarg_overlapping_positional(self):
        class Foo:
            def bar(self, a, b, c=1, **kwargs):
                pass

        e = flexmock(Foo).should_receive("bar")
        assert_raises(MethodSignatureError, e.with_args, 1, 2, 3, c=2)

    def test_with_args_blows_up_on_invalid_kwarg(self):
        class Foo:
            def bar(self, a, b, c=1):
                pass

        e = flexmock(Foo).should_receive("bar")
        assert_raises(MethodSignatureError, e.with_args, 1, 2, d=2)

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
        flexmock(some_module).should_receive("SomeClass").with_args(1, 2)
        flexmock(some_module).should_receive("foo_function").with_args(1, 2)


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
        with open("file_name") as f:
            data = f.read()
        self.assertEqual("some data", data)


class TestFlexmockUnittestModern(ModernClass, unittest.TestCase):
    def _tear_down(self):
        return unittest.TestCase.tearDown(self)


class TestUnittestModern(TestFlexmockUnittestModern):
    pass


class TestPy3Features(unittest.TestCase):
    def test_mock_kwargs_only_func_mock_all(self):
        flexmock(some_module).should_receive("kwargs_only_func").with_args(
            1, bar=2, baz=3
        ).and_return(123)
        self.assertEqual(some_module.kwargs_only_func(1, bar=2, baz=3), 123)

    def test_mock_kwargs_only_func_mock_required(self):
        flexmock(some_module).should_receive("kwargs_only_func").with_args(1, bar=2).and_return(123)
        self.assertEqual(some_module.kwargs_only_func(1, bar=2), 123)

    def test_mock_kwargs_only_func_fails_if_required_not_provided(self):
        self.assertRaises(
            MethodSignatureError,
            flexmock(some_module).should_receive("kwargs_only_func").with_args,
            1,
        )


if __name__ == "__main__":
    unittest.main()
