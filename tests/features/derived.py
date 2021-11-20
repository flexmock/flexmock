"""Tests for mocking and spying derived classes."""
# pylint: disable=missing-docstring,no-self-use,no-member
from flexmock import exceptions, flexmock
from tests.some_module import DerivedClass, SomeClass
from tests.utils import assert_raises


class DerivedTestCase:
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

    @assert_raises(
        exceptions.MethodSignatureError, match=None
    )  # TODO: Should not raise exception #79
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

    @assert_raises(
        exceptions.MethodSignatureError, match=None
    )  # TODO: Should not raise exception #79
    def test_spy_static_method_with_args_on_derived_class_after_spying_base_class(self):
        flexmock(SomeClass).should_call("static_method_with_args").with_args(2).and_return(2).once()
        assert SomeClass.static_method_with_args(2) == 2
        flexmock(DerivedClass).should_call("static_method_with_args").with_args(4).and_return(
            4
        ).once()  # should be twice
        assert DerivedClass().static_method_with_args(4) == 4
        assert DerivedClass.static_method_with_args(4) == 4
