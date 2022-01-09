"""Test integrations that work with unittest testcases."""
# pylint: disable=missing-docstring,no-self-use
import unittest

from tests.features import FlexmockTestCase


class TestIntegrations(FlexmockTestCase, unittest.TestCase):
    pass
