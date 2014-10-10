from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import unit_manipulation
from battlesnake.plugins.contrib.arena_master.db_api import insert_wave_in_db, \
    get_match_current_wave_id_from_db, mark_wave_as_finished_in_db, \
    update_highest_wave_in_db, mark_match_as_finished_in_db, \
    mark_match_as_destroyed_in_db, insert_match_in_db
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.defines import \
    WAVE_DIFFICULTY_LEVELS
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.map_generation import \
    generate_new_muxmap
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    spawn_wave
from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    check_unit_for_fixer_use
from battlesnake.plugins.contrib.arena_master.puppets.announcing import \
    announce_arena_state_change
from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_IN_BETWEEN, GAME_STATE_ACTIVE, GAME_STATE_FINISHED, \
    GAME_STATE_STAGING
from battlesnake.plugins.contrib.arena_master.puppets.puppet import \
    ArenaMasterPuppet
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.rewards import \
    reward_salvage_for_wave, reward_blueprints_to_participants
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.ai_strategic_logic import \
    handle_ai_target_change, move_idle_units
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF


class WaveSurvivalPuppet(ArenaMasterPuppet):

    MODE_INGAME_ATTRIB_MAP = {
        'CURRENT_WAVE.D': 'current_wave',
    }

    def __init__(self, protocol, dbref):
        super(WaveSurvivalPuppet, self).__init__(protocol, dbref)

        ## Wave survival stuff.
        # This is the faction that the arena puppet has control of.
        self.attacking_faction_dbref = ATTACKER_FACTION_DBREF
        # And our protagonists.
        self.defending_faction_dbref = DEFENDER_FACTION_DBREF
        self.current_wave = None
        # This is used to stop the ActiveArenaChecksTimer from overzealously
        # declaring a match over before we either have unit data or before
        # a wave has spawned.
        self.wave_check_cooldown_counter = settings['arena_master']['wave_check_cooldown']

    def get_ingame_attr_map(self):
        retval = super(WaveSurvivalPuppet, self).get_ingame_attr_map()
        retval.update({
            'CURRENT_WAVE.D': 'current_wave',
        })
        return retval

    @inlineCallbacks
    def load_arena_from_ingame_obj(self):
        yield super(WaveSurvivalPuppet, self).load_arena_from_ingame_obj()
        self.current_wave = int(self.current_wave)

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

    def get_salvage_loss_percentage(self):
        """
        :rtype: int
        :returns: A number from 0-100 representing the approximate
            percentage of salvage that will be lost.
        """

        return WAVE_DIFFICULTY_LEVELS[self.difficulty_level]['salvage_loss']

    def get_blueprint_probabilities(self):
        """
        :rtype: int
        :return: Returns a percent value in the 0-100 range for drawing
            a random blueprint. This will eventually be expanded to include
            rarity selection.
        """

        return WAVE_DIFFICULTY_LEVELS[self.difficulty_level]['base_bp_draw_chance']

    @inlineCallbacks
    def change_state_to_active(self):
        """
        This always gets called from the In-Between state. Changes to Active
        state, poops out a wave of units.
        """

        p = self.protocol
        assert self.game_state == GAME_STATE_IN_BETWEEN, \
            "Can only go Active from In-Between."
        self.save_player_tics()
        yield self.repair_all_defending_units()
        # Auto-generate and load a new map.
        yield self.change_map(generate_new_muxmap())
        self.wave_check_cooldown_counter = settings['arena_master']['wave_check_cooldown']
        yield self.change_game_state(GAME_STATE_ACTIVE)
        message = "%ch%crWARNING: %cwAttacker wave %cc{wave_num}%cw has arrived!%cn".format(
            wave_num=self.current_wave)
        self.pemit_throughout_zone(message)
        defenders_bv2 = self.calc_total_defending_units_bv2()
        spawned_units = yield spawn_wave(
            p, self.current_wave, defenders_bv2, self.difficulty_level, self)

        message = (
            "Arena %cc{arena_id}%cw has started wave {wave_num}."
        ).format(
            arena_id=self.dbref[1:],
            wave_num=self.current_wave,
        )
        yield announce_arena_state_change(p, message)
        yield insert_wave_in_db(self, spawned_units)

    @inlineCallbacks
    def change_state_to_in_between(self):
        """
        The players have dispatched all attackers, move to the next wave's
        In-Between period.
        """

        p = self.protocol
        assert self.game_state == GAME_STATE_ACTIVE, \
            "Can only go In-Between from Active."
        yield self.change_game_state(GAME_STATE_IN_BETWEEN)
        message = (
            "%chWave %cc{wave_num}%cw complete! Re-opening spawning/de-spawning. "
            "The next wave will arrive when the arena leader types %cgcontinue%cw.%cn".format(
            wave_num=self.current_wave))
        self.pemit_throughout_zone(message)

        message = (
            "Arena %cc{arena_id}%cw has completed wave {wave_num}. "
            "If you'd like to join in, go to the Arena Nexus and: %cgajoin {arena_id}%cw"
        ).format(
            arena_id=self.dbref[1:],
            wave_num=self.current_wave,
        )
        wave_id = yield get_match_current_wave_id_from_db(self)
        yield announce_arena_state_change(p, message)
        yield mark_wave_as_finished_in_db(self, was_completed=True)

        # And now for the fun stuff... rewards!
        salvage_loss = self.get_salvage_loss_percentage()
        yield reward_salvage_for_wave(p, wave_id, salvage_loss)
        bp_draw_chance = self.get_blueprint_probabilities()
        yield reward_blueprints_to_participants(p, wave_id, bp_draw_chance)

        # Back to the boring stuff.
        yield update_highest_wave_in_db(self)
        next_wave = self.current_wave + 1
        yield self.set_current_wave(next_wave)

    @inlineCallbacks
    def change_state_to_finished(self, protocol):
        """
        Our players have all either died, or they're hanging it up from
        the In-Between state.
        """

        p = protocol
        yield self.change_game_state(GAME_STATE_FINISHED)
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
    def reset_arena(self):
        """
        Completely resets the arena back to its wave 1 initial state.
        """

        p = self.protocol
        # This wraps things up as far as the DB is concerned.
        yield mark_match_as_destroyed_in_db(self)
        # This causes a new match to be created.
        self.match_id = yield insert_match_in_db(self)
        yield self.change_game_state(GAME_STATE_STAGING)
        yield self.set_current_wave(1)
        # TODO: Un-hardcode this.
        yield self.change_map('holding_area.map')
        message = (
            "%chThe arena has been restarted. The match will start when "
            "[name({leader_dbref})] types %cgbegin%cw.%cn".format(
            wave_num=self.current_wave - 1, leader_dbref=self.leader_dbref))
        self.pemit_throughout_zone(message)

        message = (
            "Arena %cc{arena_id}%cw has restarted at wave 1 in "
            "preparation for another match. If you'd like to join, go to the "
            "Arena Nexus and: %cgajoin {arena_id}%cw"
        ).format(
            arena_id=self.dbref[1:],
        )
        yield announce_arena_state_change(p, message)

    @inlineCallbacks
    def set_current_wave(self, wave_num):
        """
        Sets the current wave to a new value.

        :param int wave_num: The wave number to set.
        """

        self.current_wave = wave_num
        yield think_fn_wrappers.set_attrs(
            self.protocol, self.dbref, {'CURRENT_WAVE.D': wave_num})

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

        bv2_total = sum([unit.battle_value2 for unit in self.list_defending_units()])
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

        bv2_total = sum([unit.battle_value2 for unit in self.list_attacking_units()])
        return bv2_total

    def get_defender_spawn_coords(self):
        """
        :rtype: tuple
        :returns: A tuple of defender spawn coordinates.
        """

        return self.map_width / 2, self.map_height / 2

    @inlineCallbacks
    def repair_all_defending_units(self):
        """
        Repairs all defending units on the map.
        """

        p = self.protocol
        for unit in self.list_defending_units():
            yield unit_manipulation.heal_unit_pilot(p, unit.dbref)
            # Rather than deal with manually setting counters and fixing
            # some of the other hidden state, just reload the units entirely.
            # The map change will cause the auto-restart.
            yield think_fn_wrappers.btloadmech(
                p, unit.dbref, unit.unit_ref)

    def announce_num_units_remaining(self, exclude_unit=None):
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
        self.pemit_throughout_zone(score_msg)
