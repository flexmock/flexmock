"""Tests for argument matching."""
# pylint: disable=missing-docstring,no-self-use,no-member
import re

from flexmock import exceptions, flexmock
from flexmock._api import flexmock_teardown
from tests import some_module
from tests.some_module import SomeClass
from tests.utils import assert_raises


class ArgumentMatchingTestCase:
    def test_arg_matching_works_with_regexp(self):
        class Foo:
            def method(self, arg1, arg2):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("f")
        ).and_return("mocked")
        assert instance.method("arg1somejunkasdf", arg2="aadsfdas") == "mocked"

    def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_karg(self):
        class Foo:
            def method(self, arg1, arg2):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("a")
        ).and_return("mocked")
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod("arg1somejunkasdfa", arg2="a")\n'
                "  Expected call[1]:\tmethod(arg2=/a/, arg1=/^arg1.*asdf$/)"
            ),
        ):
            instance.method("arg1somejunkasdfa", arg2="a")

    def test_arg_matching_with_regexp_fails_when_regexp_doesnt_match_kwarg(self):
        class Foo:
            def method(self, arg1, arg2):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(
            re.compile("^arg1.*asdf$"), arg2=re.compile("a")
        ).and_return("mocked")
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod("arg1somejunkasdf", arg2="b")\n'
                "  Expected call[1]:\tmethod(arg2=/a/, arg1=/^arg1.*asdf$/)"
            ),
        ):
            instance.method("arg1somejunkasdf", arg2="b")

    def test_module_level_function_with_kwargs(self):
        flexmock(some_module).should_receive("module_function").with_args(1, y="expected")
        with assert_raises(
            exceptions.FlexmockError,
            (
                "Arguments for call module_function did not match expectations:\n"
                '  Received call:\tmodule_function(1, y="not expected")\n'
                '  Expected call[1]:\tmodule_function(y="expected", x=1)'
            ),
        ):
            some_module.module_function(1, y="not expected")

    def test_flexmock_should_match_types_on_multiple_arguments(self):
        class Foo:
            def method(self, arg1, arg2):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(str, int).and_return("ok")
        assert instance.method("some string", 12) == "ok"
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                "  Received call:\tmethod(12, 32)\n"
                "  Expected call[1]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)"
            ),
        ):
            instance.method(12, 32)
        flexmock(instance).should_receive("method").with_args(str, int).and_return("ok")
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod(12, "some string")\n'
                "  Expected call[1]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)\n"
                "  Expected call[2]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)"
            ),
        ):
            instance.method(12, "some string")
        flexmock(instance).should_receive("method").with_args(str, int).and_return("ok")
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod("string", 12, 14)\n'
                "  Expected call[1]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)\n"
                "  Expected call[2]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)\n"
                "  Expected call[3]:\tmethod(arg1=<class 'str'>, arg2=<class 'int'>)"
            ),
        ):
            instance.method("string", 12, 14)

    def test_flexmock_should_match_types_on_multiple_arguments_generic(self):
        class Foo:
            def method(self, a, b, c):  # pylint: disable=invalid-name
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(object, object, object).and_return(
            "ok"
        )
        assert instance.method("some string", None, 12) == "ok"
        assert instance.method((1,), None, 12) == "ok"
        assert instance.method(12, 14, []) == "ok"
        assert instance.method("some string", "another one", False) == "ok"
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod("string", 12)\n'
                "  Expected call[1]:\tmethod(a=<class 'object'>, "
                "b=<class 'object'>, c=<class 'object'>)"
            ),
        ):
            instance.method("string", 12)  # pylint: disable=no-value-for-parameter
        flexmock_teardown()
        flexmock(instance).should_receive("method").with_args(object, object, object).and_return(
            "ok"
        )
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                '  Received call:\tmethod("string", 12, 13, 14)\n'
                "  Expected call[1]:\tmethod(a=<class 'object'>, "
                "b=<class 'object'>, c=<class 'object'>)"
            ),
        ):
            instance.method("string", 12, 13, 14)

    def test_flexmock_should_match_types_on_multiple_arguments_classes(self):
        class Foo:
            def method(self, a, b):  # pylint: disable=invalid-name
                pass

        class Bar:
            pass

        foo_instance = Foo()
        bar_instance = Bar()
        flexmock(foo_instance).should_receive("method").with_args(object, Bar).and_return("ok")
        assert foo_instance.method("some string", bar_instance) == "ok"
        with assert_raises(
            exceptions.MethodSignatureError,
            re.compile(
                "Arguments for call method did not match expectations:\n"
                r'  Received call:\tmethod\(.+\.<locals>\.Bar object at 0x.+>, "some string"\)\n'
                r"  Expected call\[1\]:\tmethod\(a=<class 'object'>, b=<class.+\.<locals>\.Bar'>\)"
            ),
        ):
            foo_instance.method(bar_instance, "some string")
        flexmock_teardown()
        flexmock(foo_instance).should_receive("method").with_args(object, Bar).and_return("ok")
        with assert_raises(
            exceptions.MethodSignatureError,
            re.compile(
                "Arguments for call method did not match expectations:\n"
                r'  Received call:\tmethod\(12, "some string"\)\n'
                r"  Expected call\[1\]:\tmethod\(a=<class 'object'>, b=<class.+\.<locals>\.Bar'>\)"
            ),
        ):
            foo_instance.method(12, "some string")

    def test_flexmock_should_match_keyword_arguments(self):
        class Foo:
            def method(self, arg1, **kwargs):
                pass

        instance = Foo()
        flexmock(instance).should_receive("method").with_args(1, arg3=3, arg2=2).twice()
        instance.method(1, arg2=2, arg3=3)
        instance.method(1, arg3=3, arg2=2)
        flexmock_teardown()
        flexmock(instance).should_receive("method").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                "  Received call:\tmethod(arg2=2, arg3=3)\n"
                "  Expected call[1]:\tmethod(arg3=3, arg2=2, arg1=1)"
            ),
        ):
            instance.method(arg2=2, arg3=3)  # pylint: disable=no-value-for-parameter
        flexmock_teardown()
        flexmock(instance).should_receive("method").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                "  Received call:\tmethod(1, arg2=2, arg3=4)\n"
                "  Expected call[1]:\tmethod(arg3=3, arg2=2, arg1=1)"
            ),
        ):
            instance.method(1, arg2=2, arg3=4)
        flexmock_teardown()
        flexmock(instance).should_receive("method").with_args(1, arg3=3, arg2=2)
        with assert_raises(
            exceptions.MethodSignatureError,
            (
                "Arguments for call method did not match expectations:\n"
                "  Received call:\tmethod(1)\n"
                "  Expected call[1]:\tmethod(arg3=3, arg2=2, arg1=1)"
            ),
        ):
            instance.method(1)

    def test_flexmock_should_call_should_match_keyword_arguments(self):
        class Foo:
            def method(self, arg1, arg2=None, arg3=None):
                return f"{arg1}{arg2}{arg3}"

        instance = Foo()
        flexmock(instance).should_call("method").with_args(1, arg3=3, arg2=2).once()
        assert instance.method(1, arg2=2, arg3=3) == "123"

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
