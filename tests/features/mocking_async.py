"""Tests for flexmock mocking feature."""
# pylint: disable=missing-docstring,no-self-use,no-member,too-many-lines
import unittest
import pytest

from flexmock import exceptions, flexmock
from tests import some_module
from tests.utils import assert_raises


class MockingAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_mock_async_instance_method(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"
        flexmock(Class).should_receive("method").and_return("mocked_method")
        assert await Class().method() == "mocked_method"

    @pytest.mark.asyncio
    async def test_spy_async_instance_method(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"

        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(Class).should_call("method").and_return("method").once()

    @pytest.mark.asyncio
    async def test_mock_async_class_method(self):
        class Class:
            @classmethod
            async def classmethod(cls):
                return "classmethod"

        assert await Class.classmethod() == "classmethod"
        flexmock(Class).should_receive("classmethod").and_return("mocked_classmethod")
        assert await Class.classmethod() == "mocked_classmethod"

    @pytest.mark.asyncio
    async def test_mock_async_class_method_instance_mock(self):
        class Class:
            @classmethod
            async def classmethod(cls):
                return "classmethod"

        instance = Class()
        assert await instance.classmethod() == "classmethod"
        flexmock(instance).should_receive("classmethod").and_return("mocked_classmethod")
        assert await instance.classmethod() == "mocked_classmethod"

    @pytest.mark.asyncio
    async def test_spy_async_class_method(self):
        class Class:
            @classmethod
            async def classmethod(cls):
                return "classmethod"

        assert await Class.classmethod() == "classmethod"
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(Class).should_call("classmethod").and_return("classmethod").once()

        instance = Class()
        assert await instance.classmethod() == "classmethod"
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(Class).should_call("classmethod").and_return("classmethod").once()

    @pytest.mark.asyncio
    async def test_mock_async_static_method(self):
        class Class:
            @staticmethod
            async def staticmethod():
                return "staticmethod"

        assert await Class.staticmethod() == "staticmethod"
        flexmock(Class).should_receive("staticmethod").and_return("mocked_staticmethod")
        assert await Class.staticmethod() == "mocked_staticmethod"

    @pytest.mark.asyncio
    async def test_mock_async_static_method_instance_mock(self):
        class Class:
            @staticmethod
            async def staticmethod():
                return "staticmethod"

        instance = Class()
        assert await instance.staticmethod() == "staticmethod"
        flexmock(instance).should_receive("staticmethod").and_return("mocked_staticmethod")
        assert await instance.staticmethod() == "mocked_staticmethod"

    @pytest.mark.asyncio
    async def test_spy_async_static_method(self):
        class Class:
            @staticmethod
            async def staticmethod():
                return "staticmethod"

        assert await Class.staticmethod() == "staticmethod"
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(Class).should_call("staticmethod").and_return("staticmethod").once()

        instance = Class()
        assert await instance.staticmethod() == "staticmethod"
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(instance).should_call("staticmethod").and_return("staticmethod").once()

    @pytest.mark.asyncio
    async def test_mock_async_module_function(self):
        assert await some_module.async_module_function(15, 5) == 10
        flexmock(some_module).should_receive("async_module_function").and_return(20)
        assert await some_module.async_module_function(15, 5) == 20

    @pytest.mark.asyncio
    async def test_spy_async_module_function(self):
        assert await some_module.async_module_function(15, 5) == 10
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(some_module).should_call("async_module_function").and_return(10).once()

    @pytest.mark.asyncio
    async def test_mock_async_method_with_args(self):
        class Class:
            async def method(self, arg1):
                return arg1

        assert await Class().method("value") == "value"
        flexmock(Class).should_receive("method").with_args("value").and_return("mocked").once()
        assert await Class().method("value") == "mocked"

    @pytest.mark.asyncio
    async def test_spy_async_method_with_args(self):
        class Class:
            async def method(self, arg1):
                return arg1

        assert await Class().method("value") == "value"
        with assert_raises(
            exceptions.FlexmockError, ("and_return() can not be used on an async spy")
        ):
            flexmock(Class).should_call("method").with_args("value").and_return("value").once()

    @pytest.mark.asyncio
    async def test_mock_async_instance_method_can_be_called_multiple_time(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"
        flexmock(Class).should_receive("method").and_return("mocked_method")
        assert await Class().method() == "mocked_method"
        assert await Class().method() == "mocked_method"

    @pytest.mark.asyncio
    async def test_mock_async_instance_method_with_yield(self):
        class Class:
            async def method(self):
                return "method"

        assert await Class().method() == "method"

        instance = flexmock(Class())
        instance.should_receive("method").and_yield(1, 2)

        result = await instance.method()
        assert next(result) == 1
        assert next(result) == 2
