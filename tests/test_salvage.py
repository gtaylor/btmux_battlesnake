from pprint import pprint
import unittest

from battlesnake.plugins.contrib.arena_master.puppets.rewards import \
    divide_salvage


LARGELY_INTACT = {
    "Engine": 6,
    "LifeSupport": 2,
    "Armor": 50,
    "Gyro": 4,
    "ES_Internal": 79,
    "Ammo_IS.PlasmaRifle": 2,
    "IS.StreakSRM-4": 1,
    "Cockpit": 1,
    "Ammo_IS.StreakSRM-4": 1,
    "IS.PlasmaRifle": 1,
    "Actuator": 12,
    "Sensors": 2,
    "IS.SmallLaser": 1,
    "Double_HeatSink": 12,
}


class SalvageDivisionTests(unittest.TestCase):

    def test_largely_intact_division(self):

        d3li = divide_salvage(LARGELY_INTACT, 3, 94)
        print "Three-way division"
        pprint(d3li)

        print "Single division"
        d1li = divide_salvage(LARGELY_INTACT, 1, 94)
        pprint(d1li)
