from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import unit_manipulation

from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    check_unit_for_fixer_use
from battlesnake.plugins.contrib.arena_master.db_api import insert_wave_in_db, \
    mark_wave_as_finished_in_db, update_match_game_state_in_db, \
    update_match_difficulty_in_db, insert_match_in_db, \
    mark_match_as_finished_in_db, update_highest_wave_in_db, \
    mark_match_as_destroyed_in_db
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    spawn_wave
from battlesnake.plugins.contrib.arena_master.puppets.announcing import \
    announce_arena_state_change
from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_STAGING, GAME_STATE_ACTIVE, GAME_STATE_IN_BETWEEN, \
    GAME_STATE_FINISHED
from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnitStore
from battlesnake.plugins.contrib.arena_master.puppets.strategic_logic import \
    move_idle_units, handle_ai_target_change


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, protocol, dbref, map_dbref, staging_dbref, leader_dbref,
                 creator_dbref, map_height, map_width, current_wave,
                 game_mode, game_state, difficulty_level, match_id):
        self.protocol = protocol
        self.dbref = dbref
        self.map_dbref = map_dbref
        self.staging_dbref = staging_dbref
        self.leader_dbref = leader_dbref
        self.creator_dbref = creator_dbref
        # A cache for all units in the arena, plus their states.
        self.unit_store = ArenaMapUnitStore(
            arena_master_puppet=self, unit_change_callback=self.handle_unit_change)
        self.map_width = int(map_width)
        self.map_height = int(map_height)
        self.arena_name = 'Arena %s' % self.dbref[1:]
        # Currently only 'wave'.
        self.game_mode = game_mode
        # One of: 'staging', 'in-between', 'active', 'finished'
        self.game_state = game_state
        # One of: 'easy', 'normal', 'hard', 'overkill'
        self.difficulty_level = difficulty_level.lower()
        # Match ID in the DB.
        self.match_id = match_id

        ## Wave survival stuff.
        # This is the faction that the arena puppet has control of.
        self.attacking_faction_dbref = ATTACKER_FACTION_DBREF
        # And our protagonists.
        self.defending_faction_dbref = DEFENDER_FACTION_DBREF
        self.current_wave = int(current_wave)
        # This is used to stop the ActiveArenaChecksTimer from overzealously
        # declaring a match over before we either have unit data or before
        # a wave has spawned.
        self.wave_check_cooldown_counter = settings['arena_master']['wave_check_cooldown']

    def __str__(self):
        return u"<ArenaMasterPuppet: %s for map %s>" % (self.dbref, self.map_dbref)

    @property
    def id(self):
        """
        :returns: The arena ID, which is just the dbref without the # sign.
        """

        return self.dbref[1:]

    @inlineCallbacks
    def change_state_to_active(self, protocol):
        """
        This always gets called from the In-Between state. Changes to Active
        state, poops out a wave of units.
        """

        p = protocol
        assert self.game_state == GAME_STATE_IN_BETWEEN, \
            "Can only go Active from In-Between."
        self.save_defender_tics(protocol)
        yield self.change_game_state(p, GAME_STATE_ACTIVE)
        yield self.repair_all_defending_units(protocol)
        message = "%ch%crWARNING: %cwAttacker wave %cc{wave_num}%cw has arrived!%cn".format(
            wave_num=self.current_wave)
        self.pemit_throughout_zone(p, message)
        defenders_bv2 = self.calc_total_defending_units_bv2()
        yield spawn_wave(
            p, self.current_wave, defenders_bv2, self.difficulty_level, self)

        message = (
            "Arena %cc{arena_id}%cw has started wave {wave_num}."
        ).format(
            arena_id=self.dbref[1:],
            wave_num=self.current_wave,
        )
        yield announce_arena_state_change(p, message)
        yield insert_wave_in_db(self)

    @inlineCallbacks
    def change_state_to_in_between(self, protocol):
        """
        The players have dispatched all attackers, move to the next wave's
        In-Between period.
        """

        p = protocol
        assert self.game_state == GAME_STATE_ACTIVE, \
            "Can only go In-Between from Active."
        yield self.change_game_state(p, GAME_STATE_IN_BETWEEN)
        message = (
            "%chWave %cc{wave_num}%cw complete! Re-opening spawning/de-spawning. "
            "The next wave will arrive when the arena leader types %cgcontinue%cw.%cn".format(
            wave_num=self.current_wave))
        self.pemit_throughout_zone(p, message)

        message = (
            "Arena %cc{arena_id}%cw has completed wave {wave_num}. "
            "If you'd like to join in, go to the Arena Nexus and: %cgajoin {arena_id}%cw"
        ).format(
            arena_id=self.dbref[1:],
            wave_num=self.current_wave,
        )
        yield announce_arena_state_change(p, message)
        yield mark_wave_as_finished_in_db(self, was_completed=True)
        yield update_highest_wave_in_db(self)

        next_wave = self.current_wave + 1
        yield self.set_current_wave(protocol, next_wave)

    @inlineCallbacks
    def change_state_to_finished(self, protocol):
        """
        Our players have all either died, or they're hanging it up from
        the In-Between state.
        """

        p = protocol
        yield self.change_game_state(p, GAME_STATE_FINISHED)
        # TODO: Send match summary?
        mux_commands.trigger(p, self.map_dbref, 'DEST_ALL_MECHS.T')

        message = (
            "Arena %cc{arena_id}%cw has ended after "
            "surviving {wave_num} full waves."
        ).format(
            arena_id=self.dbref[1:],
            wave_num=self.current_wave - 1,
        )
        yield announce_arena_state_change(p, message)
        yield mark_wave_as_finished_in_db(self, was_completed=False)
        yield mark_match_as_finished_in_db(self)

    @inlineCallbacks
    def reset_arena(self, protocol):
        """
        Completely resets the arena back to its wave 1 initial state.
        """

        p = protocol
        # This wraps things up as far as the DB is concerned.
        yield mark_match_as_destroyed_in_db(self)
        # This causes a new match to be created.
        self.match_id = yield insert_match_in_db(self)
        yield self.change_game_state(p, GAME_STATE_STAGING)
        yield self.set_current_wave(protocol, 1)
        message = (
            "%chThe arena has been restarted. The match will start when "
            "[name({leader_dbref})] types %cgbegin%cw.%cn".format(
            wave_num=self.current_wave - 1, leader_dbref=self.leader_dbref))
        self.pemit_throughout_zone(p, message)

        message = (
            "Arena %cc{arena_id}%cw has restarted at wave 1 in "
            "preparation for another match. If you'd like to join, go to the "
            "Arena Nexus and: %cgajoin {arena_id}%cw"
        ).format(
            arena_id=self.dbref[1:],
        )
        yield announce_arena_state_change(p, message)

    @inlineCallbacks
    def change_game_state(self, protocol, new_state):
        """
        Changes the match's state.

        :param str new_state: See GAME_STATE_* defines.
        """

        new_state = new_state.lower()
        self.wave_check_cooldown_counter = settings['arena_master']['wave_check_cooldown']
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

    @inlineCallbacks
    def set_current_wave(self, protocol, wave_num):
        """
        Sets the current wave to a new value.

        :param int wave_num: The wave number to set.
        """

        self.wave_check_cooldown_counter = settings['arena_master']['wave_check_cooldown']
        self.current_wave = wave_num
        yield think_fn_wrappers.set_attrs(
            protocol, self.dbref, {'CURRENT_WAVE.D': wave_num})

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

    def list_defending_units(self, piloted_only=True):
        """
        :rtype: list
        :keyword bool piloted_only: If True, only return the units who
            are piloted (by AI or humans).
        :returns: A list of all remaining defending units still on the map.
        """

        units_by_faction = self.unit_store.list_units_by_faction(
            piloted_only=piloted_only)
        return units_by_faction.get(self.defending_faction_dbref, [])

    def calc_total_defending_units_bv2(self):
        """
        :rtype: int
        :returns: The total BV2 of all defending units left in the match.
        """

        bv2_total = sum([unit.battle_value for unit in self.list_defending_units()])
        return bv2_total

    def list_attacking_units(self, piloted_only=True):
        """
        :rtype: list
        :keyword bool piloted_only: If True, only return the units who
            are piloted (by AI or humans).
        :returns: A list of all remaining attacking units still on the map.
        """

        units_by_faction = self.unit_store.list_units_by_faction(
            piloted_only=piloted_only)
        return units_by_faction.get(self.attacking_faction_dbref, [])

    def calc_total_attacking_units_bv2(self):
        """
        :rtype: int
        :returns: The total BV2 of all attacking units left in the match.
        """

        bv2_total = sum([unit.battle_value for unit in self.list_attacking_units()])
        return bv2_total

    def get_defender_spawn_coords(self):
        """
        :rtype: tuple
        :returns: A tuple of defender spawn coordinates.
        """

        return self.map_width / 2, self.map_height / 2

    @inlineCallbacks
    def repair_all_defending_units(self, protocol):
        """
        Repairs all defending units on the map.
        """

        for unit in self.list_defending_units():
            yield unit_manipulation.repair_unit_damage(protocol, unit.dbref)
            yield unit_manipulation.heal_unit_pilot(protocol, unit.dbref)

    def announce_num_units_remaining(self, protocol, exclude_unit=None):
        """
        Announces the "score" to the arena.

        :type exclude_unit: ArenaMapUnit or None
        :keyword exclude_unit: If a unit was killed, pass it in here so that
            they won't be counted towards either of the totals. The unit isn't
            cleared from the map instantly, making this a necessary evil.
        """

        num_attackers = len([un for un in self.list_attacking_units() if un != exclude_unit])
        num_defenders = len([un for un in self.list_defending_units() if un != exclude_unit])
        score_msg = (
            "%chThere are %cy{num_attackers} attacker%(s%)%cw and "
            "%cc{num_defenders} defender%(s%)%cw remaining in play.%cn".format(
                num_attackers=num_attackers, num_defenders=num_defenders,
            )
        )
        self.pemit_throughout_zone(protocol, score_msg)

    def save_defender_tics(self, protocol):
        """
        Saves all defenders' tics.
        """

        for unit in self.list_defending_units():
            unit_manipulation.save_unit_tics_to_pilot(protocol, unit.dbref)
