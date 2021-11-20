"""Tests for mocking and spying proxied objects."""
# pylint: disable=missing-docstring,no-self-use,no-member
from flexmock import flexmock
from tests import some_module
from tests.proxy import Proxy
from tests.some_module import DerivedClass, SomeClass


class ProxiedTestCase:
    def test_mock_proxied_derived_class_with_args(self):
        # pylint: disable=not-callable,invalid-name
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

    def test_mock_proxied_module_function(self):
        # pylint: disable=not-callable
        some_module_proxy = Proxy(some_module)
        flexmock(some_module_proxy).should_receive("module_function").and_return(3).once()
        assert some_module_proxy.module_function() == 3

    def test_mock_proxied_derived_class(self):
        # pylint: disable=not-callable,invalid-name
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

    def test_mock_proxied_class_with_args(self):
        # pylint: disable=not-callable,invalid-name
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

    def test_mock_proxied_class(self):
        # pylint: disable=not-callable,invalid-name
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

    def test_spy_proxied_derived_class(self):
        # pylint: disable=not-callable,invalid-name
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
        # pylint: disable=not-callable,invalid-name
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

    def test_spy_proxied_module_function(self):
        # pylint: disable=not-callable
        some_module_proxy = Proxy(some_module)
        flexmock(some_module_proxy).should_receive("module_function").and_return(0).once()
        assert some_module_proxy.module_function(2, 2) == 0

    def test_spy_proxied_class(self):
        # pylint: disable=not-callable,invalid-name
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
        # pylint: disable=not-callable,invalid-name
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
