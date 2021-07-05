"""Flexmock exceptions."""


class FlexmockError(Exception):
    """FlexmockError"""


class MockBuiltinError(Exception):
    """MockBuiltinError"""


class MethodSignatureError(FlexmockError):
    """MethodSignatureError"""


class ExceptionClassError(FlexmockError):
    """ExceptionClassError"""


class ExceptionMessageError(FlexmockError):
    """ExceptionMessageError"""


class StateError(FlexmockError):
    """StateError"""


class MethodCallError(FlexmockError):
    """MethodCallError"""


class CallOrderError(FlexmockError):
    """CallOrderError"""
