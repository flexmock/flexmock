"""Tests for flexmock teardown."""
# pylint: disable=missing-docstring,no-self-use,no-member
from flexmock import exceptions, flexmock
from flexmock._api import UPDATED_ATTRS, flexmock_teardown
from tests import some_module
from tests.utils import assert_raises


class TeardownTestCase:
    def test_flexmock_should_properly_restore_static_methods(self):
        class User:
            @staticmethod
            def get_stuff():
                return "ok!"

        assert isinstance(User.__dict__["get_stuff"], staticmethod)
        assert User.get_stuff() == "ok!"
        flexmock(User).should_receive("get_stuff")
        assert User.get_stuff() is None
        flexmock_teardown()
        assert User.get_stuff() == "ok!"
        assert isinstance(User.__dict__["get_stuff"], staticmethod)

    def test_flexmock_should_properly_restore_undecorated_static_methods(self):
        class User:
            def get_stuff():
                return "ok!"

            get_stuff = staticmethod(get_stuff)  # pylint: disable=no-staticmethod-decorator

        assert User.get_stuff() == "ok!"
        flexmock(User).should_receive("get_stuff")
        assert User.get_stuff() is None
        flexmock_teardown()
        assert User.get_stuff() == "ok!"

    def test_flexmock_should_properly_restore_module_level_functions(self):
        flexmock(some_module).should_receive("module_function").with_args(1, 2)
        assert some_module.module_function(1, 2) is None
        flexmock_teardown()
        assert some_module.module_function(1, 2) == -1

    def test_flexmock_should_revert_new_instances_on_teardown(self):
        class User:
            pass

        class Group:
            pass

        user = User()
        group = Group()
        flexmock(Group).new_instances(user)
        assert user is Group()
        flexmock_teardown()
        assert group.__class__ is Group().__class__

    def test_flexmock_should_cleanup_added_methods_and_attributes(self):
        class Group:
            pass

        group = Group()
        flexmock(Group)
        assert "should_receive" in Group.__dict__
        assert "should_receive" not in group.__dict__
        flexmock(group)
        assert "should_receive" in group.__dict__
        flexmock_teardown()
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

        flexmock_teardown()
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

        flexmock_teardown()
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
            exceptions.MethodCallError,
            "method1() expected to be called exactly 1 time, called 0 times",
        ):
            flexmock_teardown()
        for method in UPDATED_ATTRS:
            assert method not in dir(Group)
        for method in UPDATED_ATTRS:
            assert method not in dir(User)

    def test_flexmock_teardown_called_between_tests_part1(self):
        flexmock().should_receive("method1").ordered()

    def test_flexmock_teardown_called_between_tests_part2(self):
        mock = flexmock().should_receive("method2").ordered().mock()
        # Raises CallOrderError if flexmock teardown is not automatically called
        # after test part 1 above
        mock.method2()
