"""Flexmock test runner integrations."""
# pylint: disable=import-outside-toplevel
import sys
import unittest
from typing import Any, Literal, Optional, Type

from flexmock.api import flexmock_teardown


def hook_into_pytest() -> None:
    """Hook flexmock into Pytest testing framework."""
    try:
        from _pytest import runner
    except ImportError:
        pass
    else:
        saved = runner.call_runtest_hook

        def call_runtest_hook(
            item: runner.Item, when: Literal["setup", "call", "teardown"], **kwargs: Any
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
    try:
        from doctest import DocTest, DocTestRunner, TestResults
    except ImportError:
        pass
    else:
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
    try:
        # only valid TestResult class for unittest is TextTestResult
        _patch_test_result(unittest.TextTestResult)
    except Exception:  # let's not take any chances
        pass


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
