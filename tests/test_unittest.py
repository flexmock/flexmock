"""Test unittest integration."""
# pylint: disable=missing-docstring,no-self-use
import sys
import unittest

from flexmock import flexmock


class TestUnitTestIntegration(unittest.TestCase):
    """Flexmock unittest integration specific tests."""

    def test_failed_test_case(self):
        """This tests that after a successful tests, failing flexmock assertions
        will change the test result from successful to failed.
        """
        flexmock().should_receive("this_test_should_fail").once()


if __name__ == "__main__":
    EXPECTED_FAILURES = 1
    EXPECTED_TESTS = 1
    test = unittest.main(exit=False)

    if len(test.result.failures) == EXPECTED_FAILURES and test.result.testsRun == EXPECTED_TESTS:
        sys.exit(0)  # OK
    sys.exit(1)
