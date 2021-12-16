"""Test flexmock with pytest."""
# pylint: disable=missing-docstring,redefined-outer-name,no-self-use
import unittest

import pytest

from flexmock import flexmock
from flexmock._api import flexmock_teardown
from flexmock.exceptions import MethodCallError
from tests.features import FlexmockTestCase
from tests.utils import assert_raises

from . import some_module


def test_module_level_test_for_pytest():
    flexmock(foo="bar").should_receive("foo").once()
    with assert_raises(
        MethodCallError, "foo() expected to be called exactly 1 time, called 0 times"
    ):
        flexmock_teardown()


@pytest.fixture()
def runtest_hook_fixture():
    return flexmock(foo="bar").should_receive("foo").once().mock()


def test_runtest_hook_with_fixture_for_pytest(runtest_hook_fixture):
    runtest_hook_fixture.foo()


def test_flexmock_teardown_works_with_pytest_part1():
    flexmock().should_receive("method1").ordered()


def test_flexmock_teardown_works_with_pytest_part2():
    mock = flexmock().should_receive("method2").ordered().mock()
    # Raises CallOrderError if flexmock teardown is not automatically called
    # after test part 1 above
    mock.method2()


class TestForPytest(FlexmockTestCase):  # pylint: disable=too-many-ancestors
    def test_class_level_test_for_pytest(self):
        flexmock(foo="bar").should_receive("foo").once()
        with assert_raises(
            MethodCallError, "foo() expected to be called exactly 1 time, called 0 times"
        ):
            flexmock_teardown()


class TestUnittestClass(unittest.TestCase):
    def test_unittest(self):
        mocked = flexmock(a=2)
        mocked.should_receive("a").once()
        with assert_raises(
            MethodCallError, "a() expected to be called exactly 1 time, called 0 times"
        ):
            flexmock_teardown()


class TestFailureOnException:
    def _setup_failing_expectation(self):
        flexmock(foo="bar").should_receive("foo").once()

    # Use xfail to ensure we process exceptions as returned by _hook_into_pytest

    @pytest.mark.xfail(raises=RuntimeError)
    def test_exception(self):
        raise RuntimeError("TEST ERROR")

    @pytest.mark.xfail(raises=MethodCallError)
    def test_flexmock_raises_if_no_exception(self):
        self._setup_failing_expectation()

    @pytest.mark.xfail(raises=RuntimeError)
    def test_flexmock_doesnt_override_existing_exception(self):
        self._setup_failing_expectation()
        raise RuntimeError("Flexmock shouldn't suppress this exception")

    @pytest.mark.xfail(raises=AssertionError)
    def test_flexmock_doesnt_override_assertion(self):
        self._setup_failing_expectation()
        assert False, "Flexmock shouldn't suppress this assertion"


class TestAsync:
    @pytest.mark.asyncio
    async def test_mock_async_instance_method(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"
        flexmock(Class).should_receive("method").and_return("mocked_method")
        assert await Class().method() == "mocked_method"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_spy_async_instance_method(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"
        flexmock(Class).should_call("method").and_return("method").once()
        assert await Class().method() == "method"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_mock_async_class_method(self):
        class Class:
            @classmethod
            async def classmethod(cls):
                return "classmethod"

        assert await Class.classmethod() == "classmethod"
        flexmock(Class).should_receive("classmethod").and_return("mocked_classmethod")
        assert await Class.classmethod() == "mocked_classmethod"

        instance = Class()
        assert await instance.classmethod() == "classmethod"
        flexmock(instance).should_receive("classmethod").and_return("mocked_classmethod")
        assert await instance.classmethod() == "mocked_classmethod"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_spy_async_class_method(self):
        class Class:
            @classmethod
            async def classmethod(cls):
                return "classmethod"

        assert await Class.classmethod() == "classmethod"
        flexmock(Class).should_call("classmethod").and_return("classmethod").once()
        assert await Class.classmethod() == "classmethod"

        instance = Class()
        assert await instance.classmethod() == "classmethod"
        flexmock(instance).should_call("classmethod").and_return("classmethod").once()
        assert await instance.classmethod() == "classmethod"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_mock_async_static_method(self):
        class Class:
            @staticmethod
            async def staticmethod():
                return "staticmethod"

        assert await Class.staticmethod() == "staticmethod"
        flexmock(Class).should_receive("staticmethod").and_return("mocked_staticmethod")
        assert await Class.staticmethod() == "mocked_staticmethod"

        instance = Class()
        assert await instance.staticmethod() == "staticmethod"
        flexmock(instance).should_receive("staticmethod").and_return("mocked_staticmethod")
        assert await instance.staticmethod() == "mocked_staticmethod"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_spy_async_static_method(self):
        class Class:
            @staticmethod
            async def staticmethod():
                return "staticmethod"

        assert await Class.staticmethod() == "staticmethod"
        flexmock(Class).should_call("staticmethod").and_return("staticmethod").once()
        assert await Class.staticmethod() == "staticmethod"

        instance = Class()
        assert await instance.staticmethod() == "staticmethod"
        flexmock(instance).should_call("staticmethod").and_return("staticmethod").once()
        assert await instance.staticmethod() == "staticmethod"

    @pytest.mark.asyncio
    async def test_mock_async_function(self):
        assert await some_module.async_function(15, 5) == 10
        flexmock(some_module).should_receive("async_function").and_return(20)
        assert await some_module.async_function(15, 5) == 20

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_spy_async_function(self):
        assert await some_module.async_function(15, 5) == 10
        flexmock(some_module).should_call("async_function").and_return(10).once()
        assert await some_module.async_function(15, 5) == 10

    @pytest.mark.asyncio
    async def test_mock_async_method_with_args(self):
        class Class:
            async def method(self, arg1):
                return arg1

        assert await Class().method("value") == "value"
        flexmock(Class).should_receive("method").with_args("value").and_return("mocked").once()
        assert await Class().method("value") == "mocked"

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_spy_async_method_with_args(self):
        class Class:
            async def method(self, arg1):
                return arg1

        assert await Class().method("value") == "value"
        flexmock(Class).should_call("method").with_args("value").and_return("value").once()
        assert await Class().method("value") == "value"
