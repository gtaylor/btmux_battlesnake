import datetime

import simplejson

from battlesnake.conf import settings
from battlesnake.plugins.contrib.hudinfo_cache.signals import on_stale_unit_removed, \
    on_new_unit_detected, on_unit_destroyed, on_hit_landed, on_shot_missed, \
    on_unit_state_changed


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

        if 'D' in unit.status:
            # We don't track destroyed units.
            if unit.contact_id in self._unit_store:
                self.purge_unit_by_id(unit.contact_id)
            return

        if unit.contact_id not in self._unit_store:
            # New unit. Add it and let the connected clients know.
            self._unit_store[unit.contact_id] = unit
            unit_serialized = self.get_serialized_unit_by_id(unit.contact_id)
            on_new_unit_detected.send(self, unit=unit, unit_serialized=unit_serialized)
        else:
            # Compare the copy of the unit currently in the cache to the
            # one we just got from in-game.
            changes = self.compare_units(unit, self._unit_store[unit.contact_id])
            if changes:
                # This unit's state has changed. Update it.
                self._unit_store[unit.contact_id] = unit
                unit_serialized = self.get_serialized_unit_by_id(unit.contact_id)
                # Broadcast the changes to all connected users.
                on_unit_state_changed.send(
                    self, unit=unit, unit_serialized=unit_serialized,
                    changes=changes,
                )
            else:
                # No changes, but we saw the unit. Mark it so it doesn't
                # get stale purged.
                self._unit_store[unit.contact_id].mark_as_seen()

    def mark_unit_as_destroyed_by_id(self, victim_id, killer_id):
        """
        Called when a unit has been destroyed.
        """

        on_unit_destroyed.send(self, victim_id=victim_id, killer_id=killer_id)
        if victim_id in self._unit_store:
            self.purge_unit_by_id(victim_id)

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
                on_stale_unit_removed.send(self, unit=unit)
                self.purge_unit_by_id(unit.contact_id)

    def record_hit(self, victim_id, aggressor_id, weapon_name):
        """
        Records a successful attack on a unit.
        """

        on_hit_landed.send(
            self, victim_id=victim_id, aggressor_id=aggressor_id,
            weapon_name=weapon_name)

    def record_miss(self, victim_id, aggressor_id, weapon_name):
        """
        Records a missed attack on a unit.
        """

        on_shot_missed.send(
            self, victim_id=victim_id, aggressor_id=aggressor_id,
            weapon_name=weapon_name)

    def get_serialized_unit_by_id(self, unit_id):
        """
        :rtype: str
        :returns: A serialized representation of a single unit.
        """

        unit = self._unit_store[unit_id]
        return simplejson.dumps(unit, default=MapUnitEncoder.encode)

    def get_serialized_units(self):
        """
        :rtype: str
        :returns: A serialized representation of the entire unit store.
        """

        return simplejson.dumps(self._unit_store, default=MapUnitEncoder.encode)

    def compare_units(self, unit1, unit2):
        """
        Given two units of the same ID, determine what attributes (if any) are
        different between the two.

        :rtype: list
        :returns: A list of changed attributes.
        """

        unit1_dict = unit1.__dict__
        unit2_dict = unit2.__dict__
        ignored_keys = ['last_seen']
        changes = []
        for key, val in unit1_dict.items():
            if key in ignored_keys:
                continue
            unit1_val = val
            unit2_val = unit2_dict[key]
            if unit1_val != unit2_val:
                changes.append(key)
        return changes


class MapUnitEncoder(object):
    """
    Hastily thrown together encoder for MapUnit.
    """

    @staticmethod
    def encode(obj):
        if isinstance(obj, MapUnit):
            odict = obj.__dict__
            return odict
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()


class MapUnit(object):
    """
    Represents a single unit on the map. A mech, tank, vtol, suit, etc.
    """

    def __init__(self, contact_id, unit_type, mech_name, x_coord, y_coord,
                 z_coord, speed, heading, jump_heading, range_to_hex_center,
                 bearing_to_hex_center, tonnage, heat, status):
        self.contact_id = contact_id.upper()
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

    def mark_as_seen(self):
        """
        Called every time the bot sees this unit. Prevents expiration.
        """

        self.last_seen = datetime.datetime.now()

    def __repr__(self):
        return "[%s] %s" % (self.contact_id, self.mech_name)


class HudinfoCParser(object):
    """
    Parses the unit data from a "HUDINFO C" command response.
    """

    def parse(self, contact_data):
        con_split = contact_data.split(',')
        jump_heading = int(con_split[13]) if con_split[13] != '-' else None
        return MapUnit(
            contact_id=con_split[0],
            unit_type=con_split[3],
            mech_name=con_split[4],
            x_coord=int(con_split[5]),
            y_coord=int(con_split[6]),
            z_coord=int(con_split[7]),
            speed=float(con_split[10]),
            heading=int(con_split[12]),
            jump_heading=jump_heading,
            range_to_hex_center=float(con_split[14]),
            bearing_to_hex_center=int(con_split[15]),
            tonnage=int(con_split[16]),
            heat=con_split[17],
            status=con_split[18],
        )


# Lame that we have to pollute the global namespace, but whatevs.
UNIT_STORE = MapUnitStore()
