from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import think_fn_wrappers

from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    check_unit_for_fixer_use
from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnitStore
from battlesnake.plugins.contrib.arena_master.puppets.strategic_logic import \
    move_idle_units, handle_ai_target_change


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, protocol, dbref, map_dbref, staging_dbref, creator_dbref,
                 map_height, map_width, arena_name, current_wave, game_mode,
                 game_state):
        self.protocol = protocol
        self.dbref = dbref
        self.map_dbref = map_dbref
        self.staging_dbref = staging_dbref
        self.creator_dbref = creator_dbref
        # A cache for all units in the arena, plus their states.
        self.unit_store = ArenaMapUnitStore(
            arena_master_puppet=self, unit_change_callback=self.handle_unit_change)
        # This is the faction that the arena puppet has control of.
        self.attacking_faction_dbref = ATTACKER_FACTION_DBREF
        # And our protagonists.
        self.defending_faction_dbref = DEFENDER_FACTION_DBREF
        self.map_width = int(map_width)
        self.map_height = int(map_height)
        self.arena_name = arena_name
        self.current_wave = int(current_wave)
        self.game_mode = game_mode
        # One of: 'Staging', 'In-Between', 'Active', 'Finished'
        self.game_state = game_state

    def __str__(self):
        return u"<ArenaMasterPuppet: %s for map %s>" % (self.dbref, self.map_dbref)

    @inlineCallbacks
    def change_game_state(self, protocol, new_state):
        """
        Changes the match's state.

        :param str new_state: One of 'Staging', 'In-Between', 'Active', or
            'Finished'.
        """

        self.game_state = new_state
        attrs = {'GAME_STATE.D': new_state}
        yield think_fn_wrappers.set_attrs(protocol, self.dbref, attrs)

    def pemit_throughout_zone(self, protocol, message):
        """
        Sends a message to the entire arena.

        :param str message: The message to send.
        """

        announce_cmd = "@dol [zwho({dbref})]=@pemit ##={message}".format(
            dbref=self.dbref, message=message)
        protocol.write(announce_cmd)

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

        if not new_unit.is_ai:
            if 'x_coord' in changes or 'y_coord' in changes:
                check_unit_for_fixer_use(self, new_unit)

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
        defending_units = units_by_faction.get(self.defending_faction_dbref, [])

        attacking_ai_units = [unit for unit in attacking_units if unit.is_ai]
        # Put any idle/slacking units to work.
        move_idle_units(self, attacking_ai_units, defending_units)

    def list_defending_units(self):
        """
        :rtype: list
        :returns: A list of all remaining defending units still on the map.
        """

        units_by_faction = self.unit_store.list_units_by_faction()
        return units_by_faction.get(self.defending_faction_dbref, [])

    def get_defender_spawn_coords(self):
        """
        :rtype: tuple
        :returns: A tuple of defender spawn coordinates.
        """

        return self.map_width / 2, self.map_height / 2
