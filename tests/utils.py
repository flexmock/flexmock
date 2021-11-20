"""Utility functions for testing."""
from contextlib import contextmanager
from typing import Type, Union

from flexmock._api import RE_TYPE


@contextmanager
def assert_raises(expected_exception: Type[BaseException], match: Union[RE_TYPE, str, None]):
    """Assert that code raises the correct exception with a correct error message.

    Args:
        expected_exception: Type of the expected exception.
        match: String or pattern to match the error message against. Use None
          to skip error message checking.
    """
    try:
        yield
    except Exception as raised_exception:
        if not isinstance(raised_exception, expected_exception):
            raise AssertionError(
                f"Expected exception '{type(expected_exception)}' "
                f"but '{type(raised_exception)}' was raised"
            ) from raised_exception
        if match is not None:
            fail = False
            if isinstance(match, RE_TYPE):
                fail = not match.search(str(raised_exception))
                match = match.pattern
            else:
                fail = str(raised_exception) != str(match)
            if fail:
                raise AssertionError(
                    f"Expected error message:\n{'-'*39}\n'{str(match)}'\n"
                    f"\nBut got:\n\n'{str(raised_exception)}'\n{'-'*39}\n"
                ) from raised_exception
    else:
        raise AssertionError(f"Exception '{expected_exception.__name__}' not raised")
