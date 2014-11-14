from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import unit_manipulation
from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions
from battlesnake.outbound_commands.unit_manipulation import \
    restore_mechprefs_on_unit

from battlesnake.plugins.contrib.arena_master.db_api import \
    update_match_game_state_in_db, \
    update_match_difficulty_in_db
from battlesnake.plugins.contrib.arena_master.puppets.kill_tracking import \
    record_kill
from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnitStore


class ArenaMasterPuppet(object):
    """
    This is a base class for Arena Master puppets. Each game mode sub-classes
    this. We use it to track game state, and have methods for various events.
    """

    def __init__(self, protocol, dbref):
        self.protocol = protocol
        self.dbref = dbref
        self.arena_name = 'Arena %s' % self.dbref[1:]

        self.map_dbref = None
        self.staging_dbref = None
        self.puppet_ol_dbref = None
        self.leader_dbref = None
        self.creator_dbref = None
        # A cache for all units in the arena, plus their states.
        self.unit_store = None
        self.map_width = None
        self.map_height = None
        # Currently only 'wave'.
        self.game_mode = None
        # One of: 'staging', 'in-between', 'active', 'finished'
        self.game_state = None
        # One of: 'easy', 'normal', 'hard', 'overkill'
        self.difficulty_level = None
        # Match ID in the DB.
        self.match_id = None

    def __str__(self):
        return u"<ArenaMasterPuppet: %s for map %s>" % (self.dbref, self.map_dbref)

    def get_ingame_attr_map(self):
        """
        This method maps attributes on the in-game arena master puppet to
        attributes on this instance. The keys are the in-game attribute names,
        the values are the instance attribute names.

        :rtype: dict
        """

        return {
            'MAP.DBREF': 'map_dbref',
            'LEADER.DBREF': 'leader_dbref',
            'CREATOR.DBREF': 'creator_dbref',
            'STAGING_ROOM.DBREF': 'staging_dbref',
            'PUPPET_OL.DBREF': 'puppet_ol_dbref',
            'GAME_MODE.D': 'game_mode',
            'GAME_STATE.D': 'game_state',
            'DIFFICULTY_LEVEL.D': 'difficulty_level',
            'MATCH_ID.D': 'match_id',
        }

    @inlineCallbacks
    def load_arena_from_ingame_obj(self):
        """
        Pulls all of the attributes mentioned in the attribute map and sets them
        to the appropriate variables on the instance.
        """

        p = self.protocol
        ingame_attr_map = self.get_ingame_attr_map()
        ingame_attrs = yield think_fn_wrappers.get_attrs(
            p, self.dbref, ingame_attr_map.keys())
        # Convert attribute keys to ArenaMasterPuppet kwargs.
        arena_kwargs = {ingame_attr_map[k]: v for k, v in ingame_attrs.items()}
        for attr, val in arena_kwargs.items():
            setattr(self, attr, val)

        self.difficulty_level = self.difficulty_level.lower()
        self.map_width, self.map_height = yield get_map_dimensions(
            p, arena_kwargs['map_dbref'])
        self.unit_store = ArenaMapUnitStore(
            arena_master_puppet=self, unit_change_callback=self.handle_unit_change)

    @property
    def id(self):
        """
        :returns: The arena ID, which is just the dbref without the # sign.
        """

        return self.dbref[1:]

    @inlineCallbacks
    def change_game_state(self, new_state):
        """
        Changes the match's state.

        :param str new_state: See GAME_STATE_* defines.
        """

        new_state = new_state.lower()
        self.game_state = new_state
        attrs = {'GAME_STATE.D': new_state}
        yield think_fn_wrappers.set_attrs(self.protocol, self.dbref, attrs)
        yield update_match_game_state_in_db(self)

    @inlineCallbacks
    def set_difficulty(self, new_difficulty):
        """
        Sets the difficulty level for an arena.

        :param float new_difficulty: See ARENA_DIFFICULTY_LEVEL's keys.
        """

        self.difficulty_level = new_difficulty
        attrs = {'DIFFICULTY_LEVEL.D': self.difficulty_level}
        yield think_fn_wrappers.set_attrs(self.protocol, self.dbref, attrs)
        yield update_match_difficulty_in_db(self)
        message = (
            "%ch[name({leader_dbref})] has set the difficulty "
            "level to: %cy{difficulty}%cn".format(
                leader_dbref=self.leader_dbref, difficulty=new_difficulty))
        self.pemit_throughout_zone(message)

    @inlineCallbacks
    def set_arena_leader(self, new_leader):
        """
        Changes an arena's leader.

        :param str new_leader: A valid player dbref.
        """

        self.leader_dbref = new_leader
        attrs = {'LEADER.DBREF': new_leader}
        yield think_fn_wrappers.set_attrs(self.protocol, self.dbref, attrs)

    def pemit_throughout_zone(self, message):
        """
        Sends a message to the entire arena.

        :param str message: The message to send.
        """

        # We do the setdiff() here to remove dupes.
        announce_cmd = "@dol [setdiff(zwho({dbref}),)]=@pemit ##={message}".format(
            dbref=self.dbref, message=message)
        self.protocol.write(announce_cmd)

    def do_strategic_tic(self):
        """
        For now, we use smallish maps and get the AI to stumble into the
        defenders. We could get smarter and more precise down the road,
        but this will do for now.
        """

        raise NotImplementedError("Implement do_strategic_tic()")

    def save_player_tics(self):
        """
        Saves all human player tics.
        """

        for unit in self.unit_store.list_human_units():
            unit_manipulation.save_unit_tics_to_pilot(self.protocol, unit)
            unit_manipulation.save_unit_mechprefs_to_pilot(self.protocol, unit)

    @inlineCallbacks
    def change_map(self, mmap_or_mapname):
        """
        Changes the currently loaded map.

        :param mmap_or_mapname: The generated map to load.
        :type mmap_or_mapname: MuxMap or str
        """

        p = self.protocol
        if isinstance(mmap_or_mapname, str):
            # This yanks all units off of the map.
            yield think_fn_wrappers.btloadmap(p, self.map_dbref, mmap_or_mapname)
            self.map_width, self.map_height = yield get_map_dimensions(
                p, self.map_dbref)
        else:
            yield self._populate_arena_map_from_memory(mmap_or_mapname)
            self.map_width, self.map_height = mmap_or_mapname.dimensions

        # Now we'll put all of the units back on the map.
        for unit in self.unit_store.list_all_units():
            yield think_fn_wrappers.btsetxy(
                p, unit.dbref, self.map_dbref,
                self.map_width / 2, self.map_height / 2)
            if unit.pilot_dbref:
                restore_mechprefs_on_unit(p, unit)
                mux_commands.force(p, unit.pilot_dbref, 'startup')
        # And reload the staging and puppet OLs.
        yield self.reload_observers()

    @inlineCallbacks
    def _populate_arena_map_from_memory(self, mmap):
        """
        Given a MuxMap instance, populate the arena's map from it.

        :param MuxMap mmap: The in-memory map instance containing all of
            the terrain/elevation data.
        """

        p = self.protocol
        map_name = '%sx%s' % mmap.dimensions
        # This yanks all units off of the map.
        yield think_fn_wrappers.btloadmap(p, self.map_dbref, map_name)
        # Feed terrain in via btsetmaphex() a whole line at a time.
        for y in range(0, mmap.get_map_height()):
            yield think_fn_wrappers.btsetmaphex_line(
                p, self.map_dbref, y,
                mmap.terrain_list[y], mmap.elevation_list[y])

    def clear_all_powerups(self):
        """
        Clears all powerups off the map.
        """

        for powerup in self.unit_store.list_powerup_units():
            mux_commands.trigger(self.protocol, powerup.dbref, 'DESTMECH.T')

    @inlineCallbacks
    def reload_observers(self):
        """
        Reloads the observation lounges. This is currently only Staging
        and the Puppet OL.
        """

        p = self.protocol
        map_width, map_height = yield get_map_dimensions(p, self.map_dbref)
        for ol_dbref in [self.staging_dbref, self.puppet_ol_dbref]:
            yield think_fn_wrappers.btsetxy(
                p, ol_dbref, self.map_dbref, map_width / 2, map_height / 2)
            mux_commands.force(p, ol_dbref, 'startup ov')

    #
    ## Begin event handling
    #

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

        raise NotImplementedError("Implement handle_unit_change()")

    @inlineCallbacks
    def handle_unit_destruction(self, victim_unit, killer_unit):
        """
        Triggered when a unit is destroyed. Human, AI, or otherwise.

        :type victim_unit: ArenaMapUnit or None
        :param victim_unit: The unit who was killed.
        :type killer_unit: ArenaMapUnit or None
        :param killer_unit: The unit who did the killing.
        """

        if not (victim_unit and killer_unit):
            # TODO: We probably want to handle this somehow. Could have been
            # killed by the environment or @damage.
            return

        yield record_kill(self, victim_unit, killer_unit)
