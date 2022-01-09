"""Test TeamCity (PyCharm) integration."""
# pylint: disable=missing-docstring,no-self-use
import unittest

from teamcity.unittestpy import TeamcityTestRunner

from tests.features import FlexmockTestCase


class TestTeamCityTeardown(FlexmockTestCase, unittest.TestCase):
    """Test flexmock teardown works with TeamCity test runner (PyCharm)."""


if __name__ == "__main__":
    runner = TeamcityTestRunner()
    unittest.main(testRunner=runner)
