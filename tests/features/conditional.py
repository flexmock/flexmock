"""Tests for conditional assertions."""
# pylint: disable=missing-docstring,no-self-use,no-member
import functools

from flexmock import exceptions, flexmock
from tests.utils import assert_raises


class ConditionalAssertionsTestCase:
    def test_state_machine(self):
        class Radio:
            def __init__(self):
                self.is_on = False
                self.volume = 0

            def switch_on(self):
                self.is_on = True

            def switch_off(self):
                self.is_on = False

            def select_channel(self):
                return None

            def adjust_volume(self, num):
                self.volume = num

        radio = Radio()
        flexmock(radio)

        def radio_is_on():
            return radio.is_on

        radio.should_receive("select_channel").once().when(lambda: radio.is_on)
        radio.should_call("adjust_volume").once().with_args(5).when(radio_is_on)

        with assert_raises(
            exceptions.StateError,
            "select_channel expected to be called when lambda: radio.is_on is True",
        ):
            radio.select_channel()
        with assert_raises(
            exceptions.StateError, "adjust_volume expected to be called when radio_is_on is True"
        ):
            radio.adjust_volume(5)
        radio.is_on = True
        radio.select_channel()
        radio.adjust_volume(5)

    def test_when_parameter_should_be_callable(self):
        with assert_raises(exceptions.FlexmockError, "when() parameter must be callable"):
            flexmock().should_receive("something").when(1)

    def test_flexmock_should_not_blow_up_with_builtin_in_when(self):
        # It is not possible to get source for builtins. Flexmock should handle
        # this gracefully.
        mock = flexmock()
        mock.should_receive("something").when(functools.partial(lambda: False))
        with assert_raises(
            exceptions.StateError, "something expected to be called when condition is True"
        ):
            # Should not raise TypeError
            mock.something()
