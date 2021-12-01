"""Test doctest integration and flexmock API examples."""
# pylint: disable=missing-docstring,no-self-use
import doctest
import sys

from flexmock import _api


class Plane:

    model = "Airpy 1"
    is_flying = True

    def __init__(self):
        self.speed = 3
        self.direction = None
        self.destination = None
        self.passengers = ["user1", "user2", "user3"]

    def pilot(self):
        return self.passengers[0]

    def fly(self, direction="up", destination="Helsinki"):
        self.direction = direction
        self.destination = destination

    def land(self):
        return None

    def set_speed(self, speed):
        self.speed = speed

    def repair(self, part):
        del part

    def crash(self):
        return None

    def flight_log(self):
        for entry in ["land", "repair"]:
            yield entry

    def passenger_count(self):
        return len(self.passengers)


class BadWeatherException(Exception):
    pass


class TestDoctestTeardown:
    """Test doctest runner teardown."""

    def test_flexmock_teardown_works_with_doctest_part_1(self):
        """Part 1

        Examples:
            Part 1:

            >>> from flexmock import flexmock
            >>> flexmock().should_receive("method1").ordered()
            <flexmock._api.Expectation object at ...>
        """

    def test_flexmock_teardown_works_with_doctest_part_2(self):
        """Raises CallOrderError if flexmock teardown is not automatically called
        after test part 1 above.

        Examples:
            Part 2:

            >>> from flexmock import flexmock
            >>> mock = flexmock().should_receive("method2").ordered().mock()
            >>> mock.method2()
        """


if __name__ == "__main__":
    results1 = doctest.testmod(
        sys.modules[__name__],  # current module
        optionflags=doctest.ELLIPSIS,
    )

    results2 = doctest.testmod(
        _api,
        extraglobs={
            "Plane": Plane,
            "plane": Plane(),
            "BadWeatherException": BadWeatherException,
        },
        optionflags=doctest.ELLIPSIS,
    )

    sys.exit(bool(results1.failed + results2.failed))
