"""Flexmock tests that are not related to any particular feature."""
# pylint: disable=missing-docstring,no-self-use
from flexmock import Mock, flexmock
from flexmock._api import (
    ReturnValue,
    _format_args,
    _is_class_method,
    _is_static_method,
    _isproperty,
)
from tests.proxy import Proxy
from tests.some_module import DerivedClass, SomeClass


class CommonTestCase:
    def test_return_value_to_str(self):
        r_val = ReturnValue(value=1)
        assert str(r_val) == "1"

        r_val = ReturnValue(value=(1,))
        assert str(r_val) == "1"

        r_val = ReturnValue(value=(1, 2))
        assert str(r_val) == "(1, 2)"

        r_val = ReturnValue(value=1, raises=RuntimeError)
        assert str(r_val) == "<class 'RuntimeError'>(1)"

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
        # pylint: disable=not-callable,invalid-name
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
        # pylint: disable=not-callable,invalid-name
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

    def test_isproperty(self):
        class BaseClass:
            @property
            def method1(self):
                pass

            def method2(self):
                pass

        class ChildClass(BaseClass):
            pass

        base_instance = BaseClass()
        child_instance = ChildClass()
        assert _isproperty(base_instance, "method1") is True
        assert _isproperty(base_instance, "method2") is False
        assert _isproperty(BaseClass, "method1") is True
        assert _isproperty(BaseClass, "method2") is False
        assert _isproperty(child_instance, "method1") is True
        assert _isproperty(child_instance, "method2") is False
        assert _isproperty(ChildClass, "method1") is True
        assert _isproperty(ChildClass, "method2") is False
        assert _isproperty(Mock(), "method2") is False

    def test_format_args_supports_tuples(self):
        formatted = _format_args("method", {"kargs": ((1, 2),), "kwargs": {}})
        assert formatted == "method((1, 2))"

    def test_flexmock_should_not_explode_on_unicode_formatting(self):
        formatted = _format_args("method", {"kargs": (chr(0x86C7),), "kwargs": {}})
        assert formatted == 'method("蛇")'

    def test_return_value_should_not_explode_on_unicode_values(self):
        return_value = ReturnValue(chr(0x86C7))
        assert f"{return_value}" == '"蛇"'
        return_value = ReturnValue((chr(0x86C7), chr(0x86C7)))
        assert f"{return_value}" == '("蛇", "蛇")'

    def test_flexmock_should_yield_self_when_iterated(self):
        class ClassNoIter:
            pass

        instance = flexmock(ClassNoIter)
        assert instance is list(instance)[0]
