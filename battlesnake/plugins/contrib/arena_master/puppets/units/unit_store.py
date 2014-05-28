import datetime

from battlesnake.conf import settings
from battlesnake.plugins.contrib.arena_master.puppets.units.signals import on_stale_unit_removed, \
    on_new_unit_detected, on_unit_destroyed, on_shot_landed, on_shot_missed, \
    on_unit_state_changed


class ArenaMapUnitStore(object):
    """
    This class is responsible for storing data about the units on the map that
    the bot is observing. We cram it all in here so that it can be quickly
    and easily accessed elsewhere.
    """

    def __init__(self, arena_master_puppet):
        """
        :param ArenaMasterPuppet arena_master_puppet: The puppet that this
            store resides within.
        """

        self._unit_store = {}
        self.arena_master_puppet = arena_master_puppet

    def update_or_add_unit(self, unit):
        """
        Given a unit, add it to the store or update an existing record. Right
        now there is no difference between add and update, but we may
        eventually do something.

        :param ArenaMapUnit unit: The unit to add or update.
        """

        if 'D' in unit.status:
            # We don't track destroyed units.
            if unit.contact_id in self._unit_store:
                self.purge_unit_by_id(unit.contact_id)
            return

        if unit.contact_id not in self._unit_store:
            # New unit. Add it and let the connected clients know.
            self._unit_store[unit.contact_id] = unit
            on_new_unit_detected.send(self, unit=unit)
        else:
            # Compare the copy of the unit currently in the cache to the
            # one we just got from in-game.
            changes = self.compare_units(unit, self._unit_store[unit.contact_id])
            if changes:
                # This unit's state has changed. Update it.
                self._unit_store[unit.contact_id] = unit
                # Broadcast the changes to all connected users.
                on_unit_state_changed.send(
                    self, unit=unit, changes=changes,
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
        puller_interval = settings['arena_master']['contact_puller_interval']
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

        on_shot_landed.send(
            self, victim_id=victim_id, aggressor_id=aggressor_id,
            weapon_name=weapon_name)

    def record_miss(self, victim_id, aggressor_id, weapon_name):
        """
        Records a missed attack on a unit.
        """

        on_shot_missed.send(
            self, victim_id=victim_id, aggressor_id=aggressor_id,
            weapon_name=weapon_name)

    def compare_units(self, unit1, unit2):
        """
        Given two units of the same ID, determine what attributes (if any) are
        different between the two.

        :param ArenaMapUnit unit1:
        :param ArenaMapUnit unit2:
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


class ArenaMapUnit(object):
    """
    Represents a single unit on the map. A mech, tank, vtol, suit, etc.
    """

    def __init__(self, dbref, contact_id, unit_ref, unit_type, unit_move_type, mech_name,
                 x_coord, y_coord, z_coord, speed, heading, tonnage, heat,
                 status, status2, critstatus):
        self.dbref = dbref
        self.contact_id = contact_id.upper()
        self.unit_ref = unit_ref
        self.unit_type = unit_type
        self.unit_move_type = unit_move_type
        self.mech_name = mech_name
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.z_coord = z_coord
        self.speed = speed
        self.heading = heading
        self.tonnage = tonnage
        self.heat = heat
        self.status = status
        self.status2 = status2
        self.critstatus = critstatus

        self.last_seen = datetime.datetime.now()

    def mark_as_seen(self):
        """
        Called every time the bot sees this unit. Prevents expiration.
        """

        self.last_seen = datetime.datetime.now()

    def __repr__(self):
        return "[%s] %s" % (self.contact_id, self.mech_name)
