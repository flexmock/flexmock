"""Tests for flexmock stubbing feature."""
# pylint: disable=missing-docstring,no-self-use,no-member
from flexmock import flexmock
from flexmock._api import flexmock_teardown
from tests import some_module


class StubbingTestCase:
    def test_use_replace_with_for_callable_shortcut_kwargs(self):
        class Foo:
            def method(self):
                return "bar"

        instance = Foo()
        flexmock(instance, method=lambda: "baz")
        assert instance.method() == "baz"

    def test_should_replace_attributes_that_are_instances_of_classes(self):
        class Class1:
            pass

        class Class2:
            class1 = Class1()

        class2 = Class2()
        flexmock(class2, class1="test")
        assert class2.class1 == "test"

    def test_replace_non_callable_instance_attributes(self):
        class FooClass:
            def __init__(self):
                self.attribute = 1

        instance1 = FooClass()
        instance2 = FooClass()
        flexmock(instance1, attribute=2)
        flexmock(instance2, attribute=1)
        assert instance1.attribute == 2
        flexmock_teardown()
        assert instance1.attribute == 1

    def test_replace_non_callable_module_attributes(self):
        flexmock(some_module, MODULE_LEVEL_ATTRIBUTE="yay")
        assert some_module.MODULE_LEVEL_ATTRIBUTE == "yay"
        flexmock_teardown()
        assert some_module.MODULE_LEVEL_ATTRIBUTE == "test"

    def test_replace_non_callable_class_attributes(self):
        class FooClass:
            attribute = 1

        instance1 = FooClass()
        instance2 = FooClass()
        flexmock(instance1, attribute=2)
        assert instance1.attribute == 2
        assert instance2.attribute == 1
        flexmock_teardown()
        assert instance1.attribute == 1

    def test_fake_object_takes_properties(self):
        fake1 = flexmock(bar=property(lambda self: "baz"))
        fake2 = flexmock(foo=property(lambda self: "baz"))
        assert fake1.bar == "baz"
        assert fake2.foo == "baz"
