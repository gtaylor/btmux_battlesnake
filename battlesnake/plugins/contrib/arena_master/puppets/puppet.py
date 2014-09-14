from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import unit_manipulation
from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions

from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.db_api import \
    update_match_game_state_in_db, \
    update_match_difficulty_in_db
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
        self.map_width, self.map_height = yield get_map_dimensions(p, arena_kwargs['map_dbref'])
        self.unit_store = ArenaMapUnitStore(
            arena_master_puppet=self, unit_change_callback=self.handle_unit_change)

    @property
    def id(self):
        """
        :returns: The arena ID, which is just the dbref without the # sign.
        """

        return self.dbref[1:]

    @inlineCallbacks
    def change_game_state(self, protocol, new_state):
        """
        Changes the match's state.

        :param str new_state: See GAME_STATE_* defines.
        """

        new_state = new_state.lower()
        self.game_state = new_state
        attrs = {'GAME_STATE.D': new_state}
        yield think_fn_wrappers.set_attrs(protocol, self.dbref, attrs)
        yield update_match_game_state_in_db(self)

    @inlineCallbacks
    def set_difficulty(self, protocol, new_difficulty):
        """
        Sets the difficulty level for an arena.

        :param float new_difficulty: See ARENA_DIFFICULTY_LEVEL's keys.
        """

        self.difficulty_level = new_difficulty
        attrs = {'DIFFICULTY_LEVEL.D': self.difficulty_level}
        yield think_fn_wrappers.set_attrs(protocol, self.dbref, attrs)
        yield update_match_difficulty_in_db(self)
        message = (
            "%ch[name({leader_dbref})] has set the difficulty "
            "level to: %cy{difficulty}%cn".format(
                leader_dbref=self.leader_dbref, difficulty=new_difficulty))
        self.pemit_throughout_zone(protocol, message)

    @inlineCallbacks
    def set_arena_leader(self, protocol, new_leader):
        """
        Changes an arena's leader.

        :param str new_leader: A valid player dbref.
        """

        self.leader_dbref = new_leader
        attrs = {'LEADER.DBREF': new_leader}
        yield think_fn_wrappers.set_attrs(protocol, self.dbref, attrs)

    def pemit_throughout_zone(self, protocol, message):
        """
        Sends a message to the entire arena.

        :param str message: The message to send.
        """

        # We do the setdiff() here to remove dupes.
        announce_cmd = "@dol [setdiff(zwho({dbref}),)]=@pemit ##={message}".format(
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

        raise NotImplementedError("Implement handle_unit_change()")

    def do_strategic_tic(self):
        """
        For now, we use smallish maps and get the AI to stumble into the
        defenders. We could get smarter and more precise down the road,
        but this will do for now.
        """

        raise NotImplementedError("Implement do_strategic_tic()")

    def save_player_tics(self, protocol):
        """
        Saves all human player tics.
        """

        for unit in self.unit_store.list_human_units():
            unit_manipulation.save_unit_tics_to_pilot(protocol, unit.dbref)
