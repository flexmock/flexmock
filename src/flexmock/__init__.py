"""Flexmock testing library for Python."""
from flexmock import _integrations  # pylint: disable=unused-import
from flexmock._api import Expectation, Mock, flexmock

__all__ = [
    "Expectation",
    "Mock",
    "flexmock",
]
