"""Hook flexmock into Pytest.
Pytest is a Python test framework:
https://github.com/pytest-dev/pytest
"""

from typing import Generator, Optional

import pytest
from _pytest.runner import CallInfo, ExceptionInfo, Item, TestReport

from flexmock._api import flexmock_teardown


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: Item,  # pylint: disable=unused-argument
    call: CallInfo[None],
) -> Generator[None, None, None]:
    """Called to verify and tear down the mocks set up by flexmock.

    Args:
        item: Test item for which the hook is being called.
        call: Information about the current call phase.

    Yields:
        Control back to the pytest runner.
    """
    if call.when == "call":
        try:
            flexmock_teardown()
        except BaseException:  # pylint: disable=broad-except
            call.excinfo = call.excinfo or ExceptionInfo.from_current()
    elif call.when == "teardown":
        flexmock_teardown()

    _test_report: Optional[TestReport] = yield
