"""Test testtools integration."""
# pylint: disable=missing-docstring,no-self-use
import testtools

from tests.features import FlexmockTestCase


class TestTestoolsIntegration(FlexmockTestCase, testtools.TestCase):
    pass
