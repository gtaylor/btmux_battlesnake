from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnitStore
from battlesnake.plugins.contrib.arena_master.puppets.strategic_logic import \
    move_idle_units, handle_ai_target_change


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, protocol, dbref, map_dbref, map_height, map_width):
        self.protocol = protocol
        self.dbref = dbref
        self.map_dbref = map_dbref
        # A cache for all units in the arena, plus their states.
        self.unit_store = ArenaMapUnitStore(
            arena_master_puppet=self, unit_change_callback=self.handle_unit_change)
        # This is the faction that the arena puppet has control of.
        self.attacking_faction_dbref = ATTACKER_FACTION_DBREF
        # And our protagonists.
        self.defending_faction_dbref = DEFENDER_FACTION_DBREF
        self.map_width = int(map_width)
        self.map_height = int(map_height)

    def __str__(self):
        return u"<ArenaMasterPuppet: %s for map %s>" % (self.dbref, self.map_dbref)

    def handle_unit_change(self, old_unit, new_unit, changes):
        """
        This gets called by the unit store whenever a unit's state changes.
        We can react strategically.

        :param ArenaMapUnit old_unit: The old version of the unit in the
            store. This doesn't have the new changes that were picked up.
        :param ArenaMapUnit new_unit: The new unit instance generated from
            polling the units on the map. The store will copy over the
            changed attributes from this instance to ``old_unit`` after this
            handler runs.
        :param list changes: A list of attribute names that changed on
            the ``new_unit`` compared to ``old_unit``.
        """

        if 'target_dbref' in changes and new_unit.is_ai:
            handle_ai_target_change(self, old_unit, new_unit)

    def do_strategic_tic(self):
        """
        For now, we use smallish maps and get the AI to stumble into the
        defenders. We could get smarter and more precise down the road,
        but this will do for now.
        """

        units_by_faction = self.unit_store.list_units_by_faction()
        attacking_units = units_by_faction.get(self.attacking_faction_dbref, [])
        #defending_units = units_by_faction.get(self.defending_faction_dbref, [])

        attacking_ai_units = [unit for unit in attacking_units if unit.is_ai]
        # Put any slackers to work roaming around.
        # TODO: If they are stationary but have a lock, move them to lock.
        move_idle_units(self, attacking_ai_units)

    def get_defender_spawn_coords(self):
        """
        :rtype: tuple
        :returns: A tuple of defender spawn coordinates.
        """

        return self.map_width / 2, self.map_height / 2
