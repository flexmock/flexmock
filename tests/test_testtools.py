"""Test testtools integration."""

# pylint: disable=missing-docstring
import testtools

from tests.features import FlexmockTestCase


class TestTestoolsIntegration(FlexmockTestCase, testtools.TestCase):
    pass
