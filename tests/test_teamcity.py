"""Test TeamCity (PyCharm) integration."""
# pylint: disable=missing-docstring,no-self-use
import unittest

from teamcity.unittestpy import TeamcityTestRunner

from flexmock import flexmock


class TestTeamCityTeardown(unittest.TestCase):
    """Test flexmock teardown works with TeamCity test runner (PyCharm)."""

    def test_flexmock_teardown_works_with_pytest_part1(self):
        flexmock().should_receive("method1").ordered()

    def test_flexmock_teardown_works_with_pytest_part2(self):
        mock = flexmock().should_receive("method2").ordered().mock()
        # Raises CallOrderError if flexmock teardown is not automatically called
        # after test part 1 above
        mock.method2()


if __name__ == "__main__":
    runner = TeamcityTestRunner()
    unittest.main(testRunner=runner)
