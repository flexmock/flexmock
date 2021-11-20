"""Tests for flexmock spying feature."""
# pylint: disable=missing-docstring,no-self-use,no-member
import re

from flexmock import exceptions, flexmock
from flexmock._api import flexmock_teardown
from tests.utils import assert_raises


class SpyingTestCase:
    def test_spying_non_existent_mock_object_method_should_fail(self):
        mock = flexmock()
        with assert_raises(
            exceptions.FlexmockError,
            "Mock object does not have attribute 'method_foo'. "
            'Did you mean to call should_receive("method_foo") instead?',
        ):
            mock.should_call("method_foo")
        mock = flexmock(method_foo=lambda: "ok")
        mock.should_call("method_foo")

    def test_pass_thru_should_call_original_method_only_once(self):
        class Nyan:
            def __init__(self):
                self.value = 0

            def method(self):
                self.value += 1

        obj = Nyan()
        flexmock(obj)
        obj.should_call("method")
        obj.method()
        assert obj.value == 1

    def test_should_call_works_for_same_method_with_different_args(self):
        class Foo:
            def method(self, arg):
                pass

        instance = Foo()
        flexmock(instance).should_call("method").with_args("foo").once()
        flexmock(instance).should_call("method").with_args("bar").once()
        instance.method("foo")
        instance.method("bar")
        flexmock_teardown()

    def test_should_call_fails_properly_for_same_method_with_different_args(self):
        class Foo:
            def method(self, arg):
                pass

        instance = Foo()
        flexmock(instance).should_call("method").with_args("foo").once()
        flexmock(instance).should_call("method").with_args("bar").once()
        instance.method("foo")
        with assert_raises(
            exceptions.MethodCallError,
            'method(arg="bar") expected to be called exactly 1 time, called 0 times',
        ):
            flexmock_teardown()

    def test_should_call_alias_should_create_a_spy(self):
        class Foo:
            def get_stuff(self):
                return "yay"

        instance = Foo()
        flexmock(instance).should_call("get_stuff").and_return("yay").once()
        with assert_raises(
            exceptions.MethodCallError,
            "get_stuff() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()

    def test_spy_should_not_match_falsy_stuff(self):
        class Foo:
            def method1(self):
                return None

            def method2(self):
                return False

            def method3(self):
                return []

            def method4(self):
                return ""

        instance = Foo()
        flexmock(instance).should_call("method1").and_return("bar").once()
        flexmock(instance).should_call("method2").and_return("bar").once()
        flexmock(instance).should_call("method3").and_return("bar").once()
        flexmock(instance).should_call("method4").and_return("bar").once()
        with assert_raises(
            exceptions.FlexmockError,
            (
                "Returned values for call method1 did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\tNone"
            ),
        ):
            instance.method1()
        with assert_raises(
            exceptions.FlexmockError,
            (
                "Returned values for call method2 did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\tFalse"
            ),
        ):
            instance.method2()
        with assert_raises(
            exceptions.FlexmockError,
            (
                "Returned values for call method3 did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\t[]"
            ),
        ):
            instance.method3()
        with assert_raises(
            exceptions.FlexmockError,
            (
                "Returned values for call method4 did not match expectation:\n"
                "  Expected:\t'bar'\n"
                "  Returned:\t''"
            ),
        ):
            instance.method4()

    def test_spy_should_match_return_value_class(self):
        class User:
            pass

        user = User()
        instance = flexmock(
            foo=lambda: ("bar", "baz"),
            bar=lambda: user,
            baz=lambda: None,
            bax=lambda: None,
        )
        instance.should_call("foo").and_return(str, str)
        instance.should_call("bar").and_return(User)
        instance.should_call("baz").and_return(object)
        instance.should_call("bax").and_return(None)
        assert instance.foo() == ("bar", "baz")
        assert instance.bar() == user
        assert instance.baz() is None
        assert instance.bax() is None

    def test_flexmock_spy_should_not_clobber_original_method(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff")
        flexmock(user).should_call("get_stuff")
        assert user.get_stuff() == ("real", "stuff")

    def test_and_raise_with_value_that_is_not_a_class(self):
        class RaisesException:
            def get_stuff(self):
                raise RuntimeError("baz")

        instance = RaisesException()
        flexmock(instance).should_call("get_stuff").and_raise(RuntimeError("foo")).once()
        with assert_raises(
            exceptions.ExceptionClassError,
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
            exceptions.MethodSignatureError,
            (
                "Returned values for call get_stuff did not match expectation:\n"
                "  Expected:\t('other', 'stuff')\n"
                "  Returned:\t('real', 'stuff')"
            ),
        ):
            user.get_stuff()
        flexmock(user).should_call("get_more_stuff").and_return()
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Returned values for call get_more_stuff did not match expectation:\n"
                "  Expected:\tNone\n"
                "  Returned:\t('other', 'stuff')"
            ),
        ):
            user.get_more_stuff()

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

    def test_flexmock_should_verify_correct_spy_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return("real", "stuff")
        assert user.get_stuff() == ("real", "stuff")

    def test_flexmock_should_verify_correct_spy_regexp_return_values(self):
        class User:
            def get_stuff(self):
                return "real", "stuff"

        user = User()
        flexmock(user).should_call("get_stuff").and_return(
            re.compile("ea.*"), re.compile("^stuff$")
        )
        assert user.get_stuff() == ("real", "stuff")

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
            def __init__(self, param1, param2):
                self.param1 = param1
                self.param2 = param2
                Exception.__init__(self, param1)

            def __str__(self):
                return f"{self.param1}, {self.param2}"

        class User:
            def get_stuff(self):
                raise FakeException("1", "2")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(FakeException, "2", "1")
        with assert_raises(
            exceptions.ExceptionMessageError,
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
        flexmock_teardown()

    def test_flexmock_should_verify_spy_matches_exception_regexp_mismatch(self):
        class User:
            def get_stuff(self):
                raise Exception("123asdf345")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(Exception, re.compile("^asdf"))
        with assert_raises(
            exceptions.ExceptionMessageError,
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
                raise exceptions.CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(exceptions.MethodCallError)
        with assert_raises(
            exceptions.ExceptionClassError,
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
                raise exceptions.CallOrderError("foo")

        user = User()
        flexmock(user).should_call("get_stuff").and_raise(exceptions.FlexmockError)
        user.get_stuff()

    def test_flexmock_should_call_respects_matched_expectations(self):
        class Group:
            def method1(self, arg1, arg2="b"):
                return f"{arg1}:{arg2}"

            def method2(self, arg):
                return arg

        group = Group()
        flexmock(group).should_call("method1").twice()
        assert group.method1("a", arg2="c") == "a:c"
        assert group.method1("a") == "a:b"
        group.should_call("method2").once().with_args("c")
        assert group.method2("c") == "c"
        flexmock_teardown()

    def test_flexmock_should_call_respects_unmatched_expectations(self):
        class Group:
            def method1(self, arg1, arg2="b"):
                return f"{arg1}:{arg2}"

            def method2(self, arg1):
                pass

        group = Group()
        flexmock(group).should_call("method1").at_least().once()
        with assert_raises(
            exceptions.MethodCallError,
            "method1() expected to be called at least 1 time, called 0 times",
        ):
            flexmock_teardown()
        flexmock(group)
        group.should_call("method2").with_args("a").once()
        group.should_receive("method2").with_args("not a")
        group.method2("not a")
        with assert_raises(
            exceptions.MethodCallError,
            'method2(arg1="a") expected to be called exactly 1 time, called 0 times',
        ):
            flexmock_teardown()

    def test_flexmock_should_not_blow_up_on_should_call_for_class_methods(self):
        class User:
            @classmethod
            def method(cls):
                return "class"

        flexmock(User).should_call("method")
        assert User.method() == "class"

    def test_flexmock_should_not_blow_up_on_should_call_for_static_methods(self):
        class User:
            @staticmethod
            def method():
                return "static"

        flexmock(User).should_call("method")
        assert User.method() == "static"

    def test_should_call_with_class_default_attributes(self):
        """Flexmock should not allow mocking class default attributes like
        __call__ on an instance.
        """

        class WithCall:
            def __call__(self, arg1):
                return arg1

        instance = WithCall()

        with assert_raises(
            exceptions.FlexmockError,
            re.compile(r".+<locals>\.WithCall object at 0x.+> does not have attribute '__call__'"),
        ):
            flexmock(instance).should_call("__call__")

    def test_should_call_on_class_mock(self):
        class User:
            def __init__(self):
                self.value = "value"

            def method1(self):
                return "class"

            def method2(self):
                return self.value

        # Access class-level method
        user1 = User()
        user2 = User()
        flexmock(User).should_call("method1").once()
        with assert_raises(
            exceptions.MethodCallError,
            "method1() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()
        flexmock(User).should_call("method1").twice()
        assert user1.method1() == "class"
        assert user2.method1() == "class"

        # Access instance attributes
        flexmock(User).should_call("method2").once()
        with assert_raises(
            exceptions.MethodCallError,
            "method2() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()
        flexmock(User).should_call("method2").twice()
        assert user1.method2() == "value"
        assert user2.method2() == "value"

        # Try resetting the expectation
        flexmock(User).should_call("method2").once()
        assert user1.method2() == "value"
