import datetime

from battlesnake.conf import settings


class MapUnitStore(object):
    """
    This class is responsible for storing data about the units on the map that
    the bot is observing. We cram it all in here so that it can be quickly
    and easily accessed elsewhere.
    """

    def __init__(self):
        self._unit_store = {}

    def update_or_add_unit(self, unit):
        """
        Given a unit, add it to the store or update an existing record. Right
        now there is no difference between add and update, but we may
        eventually do something.

        :param MapUnit unit: The unit to add or update.
        """

        if unit.contact_id not in self._unit_store:
            print "New unit: %s" % unit
        self._unit_store[unit.contact_id] = unit

    def purge_unit_by_id(self, unit_id):
        """
        Completely wipes a unit from the store.

        :param str unit_id: The ID of the unit to delete.
        """

        del self._unit_store[unit_id]

    def purge_stale_units(self):
        """
        Goes through all of the units in the store, expiring any that we
        haven't seen for a while.
        """

        now = datetime.datetime.now()
        puller_interval = settings['hudinfo_cache']['contact_puller_interval']
        cutoff = now - datetime.timedelta(seconds=puller_interval * 3)
        for unit_id, unit in self._unit_store.items():
            if unit.last_seen < cutoff:
                print "Removing stale unit:", unit
                self.purge_unit_by_id(unit.contact_id)


class MapUnit(object):
    """
    Represents a single unit on the map. A mech, tank, vtol, suit, etc.
    """

    def __init__(self, contact_id, unit_type, mech_name, x_coord, y_coord,
                 z_coord, speed, heading, jump_heading, range_to_hex_center,
                 bearing_to_hex_center, tonnage, heat, status):
        self.contact_id = contact_id
        self.unit_type = unit_type
        self.mech_name = mech_name
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.z_coord = z_coord
        self.speed = speed
        self.heading = heading
        self.jump_heading = jump_heading
        self.range_to_hex_center = range_to_hex_center
        self.bearing_to_hex_center = bearing_to_hex_center
        self.tonnage = tonnage
        self.heat = heat
        self.status = status

        self.last_seen = datetime.datetime.now()

    def __repr__(self):
        return "[%s] %s" % (self.contact_id, self.mech_name)


class HudinfoCParser(object):
    """
    Parses the unit data from a "HUDINFO C" command response.
    """

    def parse(self, contact_data):
        con_split = contact_data.split(',')
        return MapUnit(
            contact_id=con_split[0],
            unit_type=con_split[3],
            mech_name=con_split[4],
            x_coord=con_split[5],
            y_coord=con_split[6],
            z_coord=con_split[7],
            speed=con_split[10],
            heading=con_split[12],
            jump_heading=con_split[13],
            range_to_hex_center=con_split[14],
            bearing_to_hex_center=con_split[15],
            tonnage=con_split[16],
            heat=con_split[17],
            status=con_split[18],
        )


# Lame that we have to pollute the global namespace, but whatevs.
UNIT_STORE = MapUnitStore()
