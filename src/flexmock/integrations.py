"""Flexmock test runner integrations."""
# pylint: disable=import-outside-toplevel
import sys
import unittest
from contextlib import suppress
from typing import Any, Optional, Type

from typing_extensions import Literal

from flexmock.api import flexmock_teardown


def hook_into_pytest() -> None:
    """Hook flexmock into Pytest.

    Pytest is a Python test framework:
    https://github.com/pytest-dev/pytest
    """
    with suppress(ImportError):
        from _pytest import runner
        saved = runner.call_runtest_hook

        def call_runtest_hook(
            item: runner.Item, when: Literal["setup", "call", "teardown"], **kwargs: Any,
        ) -> runner.CallInfo[None]:
            ret = saved(item, when, **kwargs)
            if when != "call" and ret.excinfo is None:
                return ret
            teardown = runner.CallInfo.from_call(flexmock_teardown, when=when)
            teardown.duration = ret.duration
            if ret.excinfo is not None:
                teardown.excinfo = ret.excinfo
            return teardown

        runner.call_runtest_hook = call_runtest_hook


def hook_into_doctest() -> None:
    """Hook flexmock into doctest."""
    with suppress(ImportError):
        from doctest import DocTest, DocTestRunner, TestResults
        saved = DocTestRunner.run

        def run(
            self: DocTestRunner,
            test: DocTest,
            compileflags: Optional[int] = None,
            out: Optional[Any] = None,
            clear_globs: bool = True,
        ) -> TestResults:
            try:
                return saved(self, test, compileflags, out, clear_globs)
            finally:
                flexmock_teardown()

        DocTestRunner.run = run  # type: ignore


def hook_into_unittest() -> None:
    """Hook flexmock into unittest."""
    # only valid TestResult class for unittest is TextTestResult
    _patch_test_result(unittest.TextTestResult)


def hook_into_teamcity_unittest() -> None:
    """Hook into Teamcity unittests. This allows flexmock to be used within PyCharm."""
    with suppress(ImportError):
        from tcunittest import TeamcityTestResult
        _patch_test_result(TeamcityTestResult)


def hook_into_testtools() -> None:
    """Hook into teststools.

    testtools is a set of extensions to the Python standard library's unit testing framework:
    https://github.com/testing-cabal/testtools
    """
    with suppress(ImportError):
        from testtools import testresult
        _patch_test_result(testresult.TestResult)


def hook_into_zope() -> None:
    """Hook into Zope testrunner.

    Zope is an open-source web application server:
    https://github.com/zopefoundation/Zope
    """
    with suppress(ImportError):
        from zope import testrunner
        _patch_test_result(testrunner.runner.TestResult)


def hook_into_subunit() -> None:
    """Hook into subunit.

    Subunit is a test reporting and controlling protocol.
    https://github.com/testing-cabal/subunit
    """
    with suppress(ImportError):
        import subunit
        _patch_test_result(subunit.TestProtocolClient)


def hook_into_twisted() -> None:
    """Hook into twisted.

    Twisted is an event-based framework for internet applications:
    https://github.com/twisted/twisted
    """
    with suppress(ImportError):
        from twisted.trial import reporter
        _patch_test_result(reporter.MinimalReporter)
        _patch_test_result(reporter.TextReporter)
        _patch_test_result(reporter.VerboseTextReporter)
        _patch_test_result(reporter.TreeReporter)


def _patch_test_result(klass: Type[unittest.TextTestResult]) -> None:
    """Patches flexmock into any class that inherits unittest.TestResult.

    This seems to work well for majority of test runners. In the case of nose
    it's not even necessary as it doesn't override unittest.TestResults's
    addSuccess and addFailure methods so simply patching unittest works
    out of the box for nose.

    For those that do inherit from unittest.TestResult and override its
    stopTest and addSuccess methods, patching is pretty straightforward
    (numerous examples below).

    The reason we don't simply patch unittest's parent TestResult class
    is stopTest and addSuccess in the child classes tend to add messages
    into the output that we want to override in case flexmock generates
    its own failures.
    """
    # pylint: disable=invalid-name
    saved_addSuccess = klass.addSuccess
    saved_stopTest = klass.stopTest

    def addSuccess(self: unittest.TextTestResult, _test: unittest.TestCase) -> None:
        self._pre_flexmock_success = True  # type: ignore

    def stopTest(self: unittest.TextTestResult, test: unittest.TestCase) -> None:
        if saved_stopTest.__code__ is not stopTest.__code__:
            # if parent class was for some reason patched, avoid calling
            # flexmock_teardown() twice and delegate up the class hierarchy
            # this doesn't help if there is a gap and only the parent's
            # parent class was patched, but should cover most screw-ups
            try:
                flexmock_teardown()
                saved_addSuccess(self, test)
            except Exception:
                if hasattr(self, "_pre_flexmock_success"):
                    self.addFailure(test, sys.exc_info())
            if hasattr(self, "_pre_flexmock_success"):
                del self._pre_flexmock_success  # type: ignore
        return saved_stopTest(self, test)

    if klass.stopTest is not stopTest:
        klass.stopTest = stopTest  # type: ignore

    if klass.addSuccess is not addSuccess:
        klass.addSuccess = addSuccess  # type: ignore
