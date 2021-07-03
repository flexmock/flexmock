"""Flexmock test runner integrations."""
# pylint: disable=import-outside-toplevel
import sys

from flexmock.api import flexmock_teardown


def hook_into_pytest():
    """Hook flexmock into Pytest testing framework."""
    try:
        from _pytest import runner

        saved = runner.call_runtest_hook

        def call_runtest_hook(item, when, **kwargs):
            ret = saved(item, when, **kwargs)
            if when != "call" and ret.excinfo is None:
                return ret
            if hasattr(runner.CallInfo, "from_call"):
                teardown = runner.CallInfo.from_call(flexmock_teardown, when=when)
                teardown.duration = ret.duration
            else:
                teardown = runner.CallInfo(flexmock_teardown, when=when)
                teardown.result = None
            if ret.excinfo is not None:
                teardown.excinfo = ret.excinfo
            return teardown

        runner.call_runtest_hook = call_runtest_hook

    except ImportError:
        pass


def hook_into_doctest():
    """Hook flexmock into doctest."""
    try:
        from doctest import DocTestRunner

        saved = DocTestRunner.run

        def run(self, test, compileflags=None, out=None, clear_globs=True):
            try:
                return saved(self, test, compileflags, out, clear_globs)
            finally:
                flexmock_teardown()

        DocTestRunner.run = run
    except ImportError:
        pass


def hook_into_unittest():
    """Hook flexmock into unittest."""
    import unittest

    try:
        # only valid TestResult class for unittest is TextTestResult
        _patch_test_result(unittest.TextTestResult)
    except Exception:  # let's not take any chances
        pass


def _patch_test_result(klass):
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

    def addSuccess(self, _test):
        self._pre_flexmock_success = True

    def stopTest(self, test):
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
                del self._pre_flexmock_success
        return saved_stopTest(self, test)

    if klass.stopTest is not stopTest:
        klass.stopTest = stopTest

    if klass.addSuccess is not addSuccess:
        klass.addSuccess = addSuccess
