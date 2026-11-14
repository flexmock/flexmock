"""Test unittest integration."""

# pylint: disable=missing-docstring
import io
import sys
import unittest

from flexmock import flexmock
from tests.features import FlexmockTestCase


class TestUnitTestIntegration(FlexmockTestCase, unittest.TestCase):
    """Flexmock unittest integration specific tests."""

    def test_failed_test_case(self):
        """This tests that after a successful tests, failing flexmock assertions
        will change the test result from successful to failed.
        """
        flexmock().should_receive("this_test_should_fail").once()


class InheritedTextTestResult(unittest.TextTestResult):
    """Exercise the patched result methods inherited by another runner."""


class TestResultReporting(unittest.TestCase):
    def _run_cases(self, names, result_class):
        class Cases(unittest.TestCase):
            def success(self):
                pass

            def failure(self):
                self.fail("test body failed")

            def error(self):
                raise RuntimeError("test body errored")

            @unittest.skip("not run")
            def skipped(self):
                pass

            @unittest.expectedFailure
            def expected_failure(self):
                self.fail("expected failure")

            @unittest.expectedFailure
            def unexpected_success(self):
                pass

            def unmet_expectation(self):
                flexmock().should_receive("not_called").once()

            def failure_with_unmet_expectation(self):
                flexmock().should_receive("not_called").once()
                self.fail("keep the original failure")

        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=result_class)
        result = runner.run(unittest.TestSuite(Cases(name) for name in names))
        return result, stream.getvalue()

    def test_success_is_reported_once(self):
        for result_class in (unittest.TextTestResult, InheritedTextTestResult):
            with self.subTest(result_class=result_class):
                result, output = self._run_cases(["success"], result_class)
                self.assertTrue(result.wasSuccessful())
                self.assertEqual(result.testsRun, 1)
                self.assertEqual(output.count("... ok\n"), 1)

    def test_other_outcomes_are_not_reported_as_success(self):
        for result_class in (unittest.TextTestResult, InheritedTextTestResult):
            for name in ("failure", "error", "skipped", "expected_failure", "unexpected_success"):
                with self.subTest(result_class=result_class, outcome=name):
                    result, output = self._run_cases([name], result_class)
                    self.assertEqual(result.testsRun, 1)
                    self.assertNotIn("ok\n", output)
                    self.assertEqual(len(result.failures), int(name == "failure"))
                    self.assertEqual(len(result.errors), int(name == "error"))
                    self.assertEqual(len(result.skipped), int(name == "skipped"))
                    self.assertEqual(len(result.expectedFailures), int(name == "expected_failure"))
                    self.assertEqual(
                        len(result.unexpectedSuccesses), int(name == "unexpected_success")
                    )

    def test_teardown_failure_replaces_a_success(self):
        for result_class in (unittest.TextTestResult, InheritedTextTestResult):
            with self.subTest(result_class=result_class):
                result, output = self._run_cases(["unmet_expectation"], result_class)
                self.assertEqual(len(result.failures), 1)
                self.assertFalse(result.wasSuccessful())
                self.assertIn("not_called() expected to be called exactly 1 time", output)
                self.assertNotIn("ok\n", output)

    def test_teardown_failure_preserves_an_existing_failure(self):
        for result_class in (unittest.TextTestResult, InheritedTextTestResult):
            with self.subTest(result_class=result_class):
                result, output = self._run_cases(["failure_with_unmet_expectation"], result_class)
                self.assertEqual(len(result.failures), 1)
                self.assertIn("keep the original failure", result.failures[0][1])
                self.assertNotIn("ok\n", output)

    def test_mixed_outcomes_do_not_leak_success_to_the_next_test(self):
        for result_class in (unittest.TextTestResult, InheritedTextTestResult):
            with self.subTest(result_class=result_class):
                names = [
                    "success",
                    "failure",
                    "error",
                    "skipped",
                    "expected_failure",
                    "unexpected_success",
                    "unmet_expectation",
                    "success",
                ]
                result, output = self._run_cases(names, result_class)
                self.assertEqual(result.testsRun, len(names))
                self.assertEqual(len(result.failures), 2)
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(len(result.skipped), 1)
                self.assertEqual(len(result.expectedFailures), 1)
                self.assertEqual(len(result.unexpectedSuccesses), 1)
                self.assertEqual(output.count("... ok\n"), 2)


if __name__ == "__main__":
    EXPECTED_FAILURES = 1
    test = unittest.main(exit=False)

    if (
        len(test.result.failures) == EXPECTED_FAILURES
        # Make sure that inherited tests are executed
        and test.result.testsRun > EXPECTED_FAILURES
    ):
        sys.exit(0)  # OK
    sys.exit(1)
