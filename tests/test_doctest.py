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


if __name__ == "__main__":
    results = doctest.testmod(
        _api,
        extraglobs={
            "Plane": Plane,
            "plane": Plane(),
            "BadWeatherException": BadWeatherException,
        },
        optionflags=doctest.ELLIPSIS,
    )
    sys.exit(results.failed)
