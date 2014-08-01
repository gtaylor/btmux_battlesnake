from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers

from battlesnake.plugins.contrib.arena_master.arena_crud.creation import \
    create_arena
from battlesnake.plugins.contrib.arena_master.arena_crud.destruction import \
    destroy_arena
from battlesnake.plugins.contrib.arena_master.db_api import \
    update_participants_in_db
from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    spawn_fixer_unit, uniformly_repair_armor, fix_all_internals, reload_all_ammo
from battlesnake.plugins.contrib.arena_master.puppets.announcing import \
    announce_arena_state_change
from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_IN_BETWEEN, ARENA_DIFFICULTY_LEVELS
from battlesnake.plugins.contrib.arena_master.puppets.kill_tracking import \
    handle_kill
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    pick_refs_for_wave, spawn_wave
from battlesnake.plugins.contrib.arena_master.puppets.salvage import \
    reward_salvage_for_wave
from battlesnake.plugins.contrib.arena_master.staging_room.idesc import \
    pemit_staging_room_idesc


class PickWaveCommand(BaseCommand):
    """
    Picks a wave full of units based on the provided conditions.
    """

    command_name = "am_pickwave"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="pickwave", description='Chooses a wave of units.')

        parser.add_argument(
            'wave_num', type=int,
            help="The wave number.")
        parser.add_argument(
            'opposing_bv2', type=int,
            help="Total BV2 of opposing force.")
        parser.add_argument(
            'difficulty_level', type=str, choices=ARENA_DIFFICULTY_LEVELS,
            help="The difficulty of the wave")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)
        refs = yield pick_refs_for_wave(
            args.wave_num, args.opposing_bv2, args.difficulty_level)
        mux_commands.pemit(protocol, invoker_dbref, str(refs))


class SpawnWaveCommand(BaseCommand):
    """
    Picks and spawns a wave full of units based on the provided conditions.
    """

    command_name = "am_spawnwave"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="spawnwave", description='Spawns a wave of units.')

        parser.add_argument(
            'wave_num', type=int,
            help="The wave number.")
        parser.add_argument(
            'opposing_bv2', type=int,
            help="Total BV2 of opposing force.")
        parser.add_argument(
            'difficulty_level', type=str, choices=ARENA_DIFFICULTY_LEVELS,
            help="Difficulty level name.")
        parser.add_argument(
            'arena_master_dbref', type=str,
            help="Arena master dbref to spawn through.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)

        arena_master_dbref = args.arena_master_dbref
        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError("Invalid arena dbref.")

        yield spawn_wave(
            protocol, args.wave_num, args.opposing_bv2, args.difficulty_level,
            puppet)
        mux_commands.pemit(protocol, invoker_dbref,
            "Spawning wave.")


class FixUnitCommand(BaseCommand):
    """
    Fixes a unit.
    """

    command_name = "am_fixunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        fixmodes = ['armor', 'ints', 'ammo']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="fixunit", description='Fixes a unit.')

        parser.add_argument(
            'mech_dbref', type=str,
            help="The dbref of the mech to fix.")
        parser.add_argument(
            'fix_percent', type=float,
            help="Percentage of damage to fix (0...1)")
        parser.add_argument(
            "--fixmode", type=str, choices=fixmodes, dest='fix_mode',
            default='armor',
            help="Determines what to fix on the unit. Defaults to armor.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        p = protocol
        mux_commands.pemit(protocol, invoker_dbref, output)

        if args.fix_mode == 'armor':
            yield uniformly_repair_armor(p, args.mech_dbref, args.fix_percent)
        elif args.fix_mode == 'ints':
            yield fix_all_internals(p, args.mech_dbref)
        elif args.fix_mode == 'ammo':
            yield reload_all_ammo(p, args.mech_dbref)


class TestUnitCommand(BaseCommand):
    """
    This is a command that can be used on an arena unit to test whatever bit
    of code we're screwing with right now.
    """

    command_name = "am_testunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="testunit", description='Does something mysterious.')

        parser.add_argument(
            'mech_dbref', type=str,
            help="The dbref of the mech to test something on.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        p = protocol
        mux_commands.pemit(p, invoker_dbref, output)

        puppet = PUPPET_STORE.find_puppet_for_unit_dbref(args.mech_dbref)
        try:
            unit = puppet.unit_store.get_unit_by_dbref(args.mech_dbref)
        except ValueError:
            raise CommandError('Unable to find unit in the unit store.')

        yield update_participants_in_db(puppet, [unit])


class SpawnFixerCommand(BaseCommand):
    """
    Spawns a fixer unit.
    """

    command_name = "am_spawnfixer"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        fixmodes = ['armor', 'ints', 'ammo']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="spawnfixer", description='Spawns a fixer unit.')

        parser.add_argument(
            'map_dbref', type=str,
            help="The dbref of the map to spawn the fixer on.")
        parser.add_argument(
            'fix_percent', type=float,
            help="Percentage of damage to fix (0...1)")
        parser.add_argument(
            "--fixertype", type=str, choices=fixmodes, dest='fixer_type',
            default='armor',
            help="Determines what to fix on the unit. Defaults to armor.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        p = protocol
        mux_commands.pemit(p, invoker_dbref, output)

        yield spawn_fixer_unit(
            p, args.map_dbref, args.fixer_type, args.fix_percent)


class CreateArenaCommand(BaseCommand):
    """
    Basic arena creation.
    """

    command_name = "am_createarena"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        self._check_for_dupe_arenas(invoker_dbref)
        mux_commands.pemit(
            p, invoker_dbref, "Please wait while we create an arena for you...")
        puppet = yield create_arena(p, invoker_dbref)
        mux_commands.pemit(p, invoker_dbref, "Your arena is ready. Good luck!")

        think_fn_wrappers.tel(p, invoker_dbref, puppet.staging_dbref)

        message = (
            "[name({leader_dbref})] has created a new arena"
            " %(ID: %ch{arena_id}%cw%). If you'd like to join, go to the "
            "Arena Nexus and: %cgajoin {arena_id}%cw"
        ).format(
            leader_dbref=invoker_dbref,
            arena_id=puppet.dbref[1:]
        )
        yield announce_arena_state_change(p, message)

    def _check_for_dupe_arenas(self, invoker_dbref):
        puppets = PUPPET_STORE.list_arena_master_puppets()
        for puppet in puppets:
            if puppet.leader_dbref == invoker_dbref:
                raise CommandError("You already have an active arena.")


class DestroyArenaCommand(BaseCommand):
    """
    Completely wipes out an arena.
    """

    command_name = "am_destroyarena"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        try:
            PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError("Invalid arena dbref.")

        mux_commands.pemit(p, invoker_dbref, "Destroying arena: %s" % arena_master_dbref)
        yield destroy_arena(p, arena_master_dbref)
        mux_commands.pemit(p, invoker_dbref, "Arena destroyed!")


class ArenaListCommand(BaseCommand):
    """
    Lists all active arenas.
    """

    command_name = "am_arenalist"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol

        puppets = PUPPET_STORE.list_arena_master_puppets()

        retval = self._get_header_str('Active Arena Listing')
        retval += self._get_footer_str('-')
        retval += (
            "%r%ch "
            "[rjust(ID,4)]%b "
            "[ljust(Arena Leader, 25)] "
            "[ljust(Difficulty, 14)]"
            "[ljust(Players,10)] "
            "State%cn"
        )
        retval += self._get_footer_str('-')
        for puppet in puppets:
            retval += (
                "%r [rjust({dbref}, 4)]%b [ljust(name({leader_dbref}),25)] "
                "[ljust({difficulty},16)] "
                "[ljust(words(zwho(#{dbref})),7)] "
                "{state}".format(
                dbref=puppet.dbref[1:], leader_dbref=puppet.leader_dbref,
                difficulty=puppet.difficulty_level.capitalize(),
                state=puppet.game_state.capitalize()))
        if not puppets:
            retval += "[center(There are no active arenas. Create one!,78)]"
        retval += self._get_footer_str()
        retval += '%r[center(To get more details on an arena%, type %ch%cgarena <id>%cn,78)]'
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)


class ArenaDetailsCommand(BaseCommand):
    """
    Command to show the details of an arena.
    """

    command_name = "am_arenadetails"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="arena", description='Shows info on an arena.')

        parser.add_argument(
            'arena_id', type=int, nargs='?', default=None,
            help="The ID of the arena to see the details for..")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, parsed_line, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    #@inlineCallbacks
    def handle(self, protocol, invoker_dbref, parsed_line, args):
        p = protocol
        invoker_zone = parsed_line.kwargs['invoker_zone']

        if args.arena_id:
            zone_dbref = '#%s' % args.arena_id
        else:
            zone_dbref = invoker_zone

        is_in_arena = invoker_zone == zone_dbref

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(zone_dbref)
        except KeyError:
            raise CommandError(
                "Invalid arena ID. See the %ch%cgarenas%cn command for a full list.")

        self.render_arena_detail(p, invoker_dbref, puppet, is_in_arena)

    def render_arena_detail(self, protocol, invoker_dbref, puppet, is_in_arena):
        render_lower_tip = is_in_arena
        pemit_staging_room_idesc(
            protocol, puppet, invoker_dbref, render_contents=False,
            render_header=True, render_lower_tip=render_lower_tip)


class ArenaJoinCommand(BaseCommand):
    """
    Joins an arena.
    """

    command_name = "am_arenajoin"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol

        arena_master_dbref = parsed_line.kwargs['arena_dbref']
        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError(
                "Invalid arena ID. See the %ch%cgarenas%cn command for a full list.")

        think_fn_wrappers.tel(p, invoker_dbref, puppet.staging_dbref)


class ContinueMatchCommand(BaseCommand):
    """
    Moves the match from in-between to the next wave.
    """

    command_name = "am_continuematch"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        if puppet.game_state != GAME_STATE_IN_BETWEEN:
            raise CommandError("You may only %ch%cgcontinue%cn when between waves.")

        yield puppet.change_state_to_active(p)


class ReportDestructionCommand(BaseCommand):
    """
    Called when a unit is destroyed.
    """

    command_name = "am_reportdestruction"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        victim_unit_dbref = parsed_line.kwargs['victim_unit_dbref']
        killer_unit_dbref = parsed_line.kwargs['killer_unit_dbref']

        print "Unit destruction reported", parsed_line.kwargs

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            # This *has* to happen.
            self._clear_corpse(p, victim_unit_dbref)
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        cause_of_death = parsed_line.kwargs['cause_of_death']
        yield handle_kill(
            p, puppet, victim_unit_dbref, killer_unit_dbref, cause_of_death)
        # This *has* to happen.
        self._clear_corpse(p, victim_unit_dbref)

    def _clear_corpse(self, p, victim_unit_dbref):
        mux_commands.trigger(p, victim_unit_dbref, 'DESTMECH.T')


class TScanCommand(BaseCommand):
    """
    Team scan, shows other units.
    """

    command_name = "am_tscan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref

        teammates = self._get_teammate_list(parsed_line, puppet)

        retval = self._get_header_str("Team Scan")
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Unit Type,15)] [ljust(Pilot Name,20)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]Cond"
        )

        retval += self._get_footer_str("-")
        for unit in teammates:
            unit_has_target = unit.target_dbref != '#-1'
            target_marker = '%ch%cr*%cn' if unit_has_target else '%b'
            armor_condition = int(unit.calc_armor_condition() * 100)
            retval += "%r"
            retval += (
                "{target_marker}%[{contact_id}%] [ljust({mech_name},15)] "
                "[ljust(name({pilot_dbref}),18)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[ljust(round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1),6)] "
                "{armor_condition}%%".format(
                    target_marker=target_marker,
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                    armor_condition=armor_condition,
                )
            )
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)

    def _get_teammate_list(self, parsed_line, puppet):
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']
        is_ol = parsed_line.kwargs.get('is_ol', False) == 'yes'

        teammates = puppet.list_defending_units()

        if is_ol:
            # OLs aren't in the puppet currently. No unit sorting.
            return teammates

        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')
        teammates.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        return teammates


class EScanCommand(BaseCommand):
    """
    Enemy scan, shows other units.
    """

    command_name = "am_escan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref

        retval = self._get_header_str("Enemy Scan", width=57)
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Unit Type,15)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]Cond"
        )

        enemies = self._get_enemy_list(parsed_line, puppet)
        retval += self._get_footer_str("-", width=57)
        for unit in enemies:
            armor_condition = int(unit.calc_armor_condition() * 100)
            retval += "%r"
            retval += (
                " %[{contact_id}%] [ljust({mech_name},13)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[ljust(round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1),6)] "
                "{armor_condition}%%".format(
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                    armor_condition=armor_condition,
                )
            )
        retval += self._get_footer_str(width=57)

        mux_commands.pemit(p, invoker_dbref, retval)

    def _get_enemy_list(self, parsed_line, puppet):
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']
        is_ol = parsed_line.kwargs.get('is_ol', False) == 'yes'

        enemies = puppet.list_attacking_units()

        if is_ol:
            # OLs aren't in the puppet currently. No unit sorting.
            return enemies

        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')
        enemies.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        return enemies


class PScanCommand(BaseCommand):
    """
    Scans for powerups.
    """

    command_name = "am_pscan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref

        retval = self._get_header_str("Powerup Scan", width=57)
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Powerup Type,15)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]"
        )

        powerups = self._get_powerup_list(parsed_line, puppet)
        retval += self._get_footer_str("-", width=57)
        for unit in powerups:
            retval += "%r"
            retval += (
                " %[{contact_id}%] [ljust({mech_name},13)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1)]".format(
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                )
            )
        retval += self._get_footer_str(width=57)

        mux_commands.pemit(p, invoker_dbref, retval)

    def _get_powerup_list(self, parsed_line, puppet):
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']
        is_ol = parsed_line.kwargs.get('is_ol', False) == 'yes'

        powerups = puppet.unit_store.list_powerup_units()

        if is_ol:
            # OLs aren't in the puppet currently. No unit sorting.
            return powerups

        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')
        powerups.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        return powerups


class TestWaveSalvageCommand(BaseCommand):
    """
    Manually trigger a salvage event on a wave.
    """

    command_name = "am_testwavesalvage"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="testsalvage", description='Manually trigger a wave salvage event.')

        parser.add_argument(
            'wave_id', type=int, nargs='?', default=None,
            help="The ID of the wave to pay out.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, parsed_line, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, parsed_line, args):
        p = protocol
        mux_commands.pemit(p, invoker_dbref, "Triggering salvage event.")
        yield reward_salvage_for_wave(protocol, args.wave_id, salvage_loss=94)


class ArenaMasterCommandTable(InboundCommandTable):

    commands = [
        TestUnitCommand,
        TestWaveSalvageCommand,

        ArenaListCommand,
        ArenaJoinCommand,
        ArenaDetailsCommand,

        ContinueMatchCommand,

        PickWaveCommand,
        SpawnWaveCommand,
        FixUnitCommand,
        SpawnFixerCommand,

        CreateArenaCommand,
        DestroyArenaCommand,

        TScanCommand,
        EScanCommand,
        PScanCommand,

        ReportDestructionCommand,
    ]
