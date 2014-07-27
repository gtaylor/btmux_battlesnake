import datetime

from battlesnake.conf import settings
from battlesnake.core.utils import calc_xy_range

from battlesnake.plugins.contrib.arena_master.puppets.units.signals import on_stale_unit_removed, \
    on_new_unit_detected, on_unit_destroyed, on_shot_landed, on_shot_missed, \
    on_unit_state_changed


class ArenaMapUnitStore(object):
    """
    This class is responsible for storing data about the units on the map that
    the bot is observing. We cram it all in here so that it can be quickly
    and easily accessed elsewhere.
    """

    def __init__(self, arena_master_puppet, unit_change_callback):
        """
        :param battlesnake.plugins.contrib.arena_master.puppets.puppet.ArenaMasterPuppet arena_master_puppet: The puppet that this
            store resides within.
        :param callable unit_change_callback: Called when a unit's state cahnges.
        """

        self._unit_store = {}
        self.arena_master_puppet = arena_master_puppet
        self.unit_change_callback = unit_change_callback

    def __iter__(self):
        for unit in self._unit_store.values():
            yield unit

    def list_all_units(self, piloted_only=False):
        """
        Non-generator way to list all units on the map.

        :keyword bool piloted_only: If True, only return units that have
            an AI or human pilot.
        :rtype: list
        :returns: A list of ArenaMapUnit instances we currently know of.
        """

        if piloted_only:
            return [unit for unit in self._unit_store.values() if unit.pilot_dbref]
        else:
            return self._unit_store.values()

    def add_unit(self, unit):
        """
        We've got a unit we haven't seen before. Add it to the store as new.

        :param ArenaMapUnit unit: The unit to add.
        """

        # New unit. Add it and let the connected clients know.
        self._unit_store[unit.contact_id] = unit
        print "New unit detected", unit
        on_new_unit_detected.send(self, unit=unit)

    def update_unit(self, new_unit):
        """
        Given a new unit received from one of the populating methods, see
        what has changed compared to what we already have locally.
        Update the values on a per-field basis instead of wholesale
        instance replacement. This preserves any AI state values we've got
        on said unit.

        :param ArenaMapUnit new_unit: The new unit data we've received.
        """

        # What we already have on file.
        old_unit = self._unit_store[new_unit.contact_id]
        # Always mark the unit as seen, regardless of if there were changes.
        old_unit.mark_as_seen()
        # Compare the copy of the unit currently in the cache to the
        # one we just got from in-game.
        changes = self.compare_units(new_unit, old_unit)
        if not changes:
            return

        # Notify the callback that a unit has changed.
        self.unit_change_callback(old_unit, new_unit, changes)

        # Update all fields that have changed.
        # This could be a lot more efficient, but we'll worry about that later.
        for change in changes:
            new_value = getattr(new_unit, change)
            setattr(old_unit, change, new_value)

        # Broadcast the changes to all connected users.
        on_unit_state_changed.send(
            self, unit=old_unit, changes=changes,
        )

    def update_or_add_unit(self, unit):
        """
        Given a unit, add it to the store or update an existing record.

        :param ArenaMapUnit unit: The unit to add or update.
        """

        if unit.is_destroyed():
            # We don't track destroyed units.
            if unit.contact_id in self._unit_store:
                self.purge_unit_by_id(unit.contact_id)
            return

        if unit.contact_id not in self._unit_store:
            self.add_unit(unit)
        else:
            self.update_unit(unit)

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

    def get_unit_by_dbref(self, dbref):
        """
        Not to be confused with :py:meth:`get_unit_by_id`, this method retrieves
        a unit by its contact ID (its designation on the map) instead of dbref.

        :param str dbref: The dbref of the unit to retrieve.
        :rtype: ArenaMapUnit
        :raises: ValueError when an invalid dbref is provided.
        """

        for unit in self:
            if unit.dbref == dbref:
                return unit
        raise ValueError('Invalid unit dbref: %s' % dbref)

    def list_powerup_units(self):
        """
        :rtype: list
        :returns: A list of powerup units.
        """

        return [unit for unit in self.__iter__() if unit.is_powerup]

    def list_units_by_faction(self, piloted_only=True):
        """
        Breaks the units up by faction into a dict of lists.

        :rtype: dict
        :returns: A dict with the keys being faction dbrefs and the values
            being a list of units belonging to said faction.
        """

        units_by_faction = {}
        for unit in self.__iter__():
            unit_faction = unit.faction_dbref
            if not unit_faction:
                continue
            if piloted_only and not unit.pilot_dbref:
                continue
            if unit_faction not in units_by_faction:
                units_by_faction[unit_faction] = []
            units_by_faction[unit_faction].append(unit)
        return units_by_faction

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
        ignored_keys = [
            'last_seen', 'ai_last_destination', 'ai_idle_counter',
            'has_been_ran_over', 'ai_optimal_weap_range',
        ]
        changes = []
        for key, val in unit1_dict.items():
            if key in ignored_keys:
                continue
            unit1_val = val
            unit2_val = unit2_dict[key]
            if unit1_val != unit2_val:
                changes.append(key)
        return changes

    def find_units_in_hex(self, x_coord, y_coord):
        """
        Given a coordinate pair, find all units in this hex.

        :rtype: list
        :returns: A list of units in the same hex.
        """

        units = []
        for unit in self.__iter__():
            if unit.x_coord != x_coord:
                continue
            if unit.y_coord != y_coord:
                continue
            units.append(unit)
        return units


class ArenaMapUnit(object):
    """
    Represents a single unit on the map. A mech, tank, vtol, suit, etc.
    """

    def __init__(self, dbref, contact_id, unit_ref, unit_type, unit_move_type,
                 mech_name, x_coord, y_coord, z_coord, speed, heading, tonnage,
                 heat, status, status2, critstatus, critstatus2, faction_dbref,
                 battle_value, target_dbref, shots_fired, shots_landed,
                 damage_inflicted, damage_taken, shots_missed, units_killed,
                 maxspeed, is_ai, pilot_dbref, is_powerup, ai_optimal_weap_range,
                 armor_int_total, hexes_walked):
        self.dbref = dbref.strip()
        self.contact_id = contact_id.strip().upper()
        self.unit_ref = unit_ref
        self.unit_type = unit_type
        self.unit_move_type = unit_move_type
        self.mech_name = mech_name
        self.x_coord = int(x_coord)
        self.y_coord = int(y_coord)
        self.z_coord = int(z_coord)
        self.speed = float(speed)
        self.heading = int(float(heading) / 32)
        self.tonnage = int(tonnage)
        self.heat = float(heat)
        self.status = status
        self.status2 = status2
        self.critstatus = critstatus
        self.critstatus2 = critstatus2
        self.faction_dbref = faction_dbref
        self.battle_value = int(float(battle_value))
        self.target_dbref = '#%s' % target_dbref
        self.shots_fired = int(shots_fired)
        self.shots_landed = int(shots_landed)
        self.shots_missed = int(shots_missed)
        self.damage_inflicted = int(damage_inflicted)
        self.damage_taken = int(damage_taken)
        self.units_killed = int(units_killed)
        self.hexes_walked = float(hexes_walked)
        self.maxspeed = float(maxspeed)
        self.is_ai = is_ai == '1'
        self.pilot_dbref = pilot_dbref
        self.is_powerup = is_powerup == '1'
        self.armor_int_total = armor_int_total

        # If the arena master wanted this unit to go somewhere, this is
        # where it last asked.
        self.ai_last_destination = None
        self.ai_idle_counter = 0
        self.ai_optimal_weap_range = int(ai_optimal_weap_range)
        # This gets set to True if the unit has been 'ran over' by a player.
        # For example, a powerup.
        self.has_been_ran_over = False

        self.last_seen = datetime.datetime.now()

    def __repr__(self):
        return "[%s] %s" % (self.contact_id, self.mech_name)

    def calc_armor_condition(self):
        """
        :rtype: float
        :returns: A 0...1 percentage of the remaining armor on the unit.
        """

        armor_totals = self.armor_int_total.split('|')[0]
        current_armor, max_armor = armor_totals.split('/')
        armor_perc = float(current_armor) / float(max_armor)
        return float('%.2f' % armor_perc)

    def distance_to_unit(self, other_unit):
        """
        Calculates the distance to another unit.

        :param ArenaMapUnit other_unit:
        :rtype: float
        :returns: Distance to other unit.
        """

        return calc_xy_range(
            self.x_coord, self.y_coord,
            other_unit.x_coord, other_unit.y_coord)

    def is_at_ai_destination(self):
        """
        :rtype: bool or None
        :returns: True if the unit is at its last specified AI destination.
            False if not, or if None if no destination has been set.
        """

        if not self.ai_last_destination:
            return
        dest_x, dest_y = self.ai_last_destination
        return self.x_coord == dest_x and self.y_coord == dest_y

    def mark_as_seen(self):
        """
        Called every time the bot sees this unit. Prevents expiration.
        """

        self.last_seen = datetime.datetime.now()

    def get_target_dbref(self):
        """
        :rtype: str or None
        :returns: The dbref of the unit's target. None if no target is locked.
            If they have a hex locked, this will be None as well.
        """

        target_dbref = self.target_dbref
        if target_dbref == '-1':
            return None
        return '#' + target_dbref

    def is_landed(self):
        return 'a' in self.status

    def is_started(self):
        return 'd' in self.status

    def is_destroyed(self):
        return 'f' in self.status

    def is_jumping(self):
        return 'g' in self.status

    def is_fallen(self):
        return self.unit_type == "Mech" and 'h' in self.status

    def is_immobile(self):
        """
        :rtype: bool
        :returns: True if this unit is incapable of moving by its primary
            means of locomotion.
        """

        if self.maxspeed == '0.0' or self.unit_move_type == 'None':
            return True
        if self.unit_type == "Vehicle" and 'h' in self.status:
            return True
        elif self.is_fallen() and self.is_gyro_destroyed():
            return True
        return False

    def is_doing_something(self):
        """
        :rtype: bool
        :returns: True if the unit's "doing something" flag has been set.
            This is only done by softcoded systems.
        """

        return 'j' in self.status

    def is_pilot_unconscious(self):
        return 'n' in self.status

    def is_masc_enabled(self):
        return 'u' in self.status

    def is_combat_safe(self):
        return 'w' in self.status

    def is_ecm_enabled(self):
        return 'a' in self.status2 or 'i' in self.status2

    def is_eccm_enabled(self):
        return 'b' in self.status2 or 'j' in self.status2

    def is_affected_by_ecm(self):
        return 'c' in self.status2 or 'l' in self.status2

    def is_protected_by_ecm(self):
        return 'd' in self.status2 or 'k' in self.status2

    def is_sprinting(self):
        return 'q' in self.status2

    def is_evading(self):
        return 'r' in self.status2

    def is_dodging(self):
        return 's' in self.status2

    def is_gyro_destroyed(self):
        return 'a' in self.critstatus or 'a' in self.critstatus2

    def is_invisible(self):
        return 'A' in self.critstatus
