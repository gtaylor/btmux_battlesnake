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
from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    spawn_fixer_unit, uniformly_repair_armor, fix_all_internals, reload_all_ammo
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    pick_refs_for_wave, spawn_wave


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
            'num_players', type=int,
            help="Number of human defenders.")
        parser.add_argument(
            'difficulty_mod', type=float,
            help="1.0 being the base level difficulty")

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
            args.wave_num, args.num_players, args.difficulty_mod)
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
            'num_players', type=int,
            help="Number of human defenders.")
        parser.add_argument(
            'difficulty_mod', type=float,
            help="1.0 being the base level difficulty.")
        parser.add_argument(
            'map_dbref', type=str,
            help="Map dbref to spawn to.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)
        yield spawn_wave(
            protocol, args.wave_num, args.num_players, args.difficulty_mod,
            args.map_dbref)
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
        invoker_name = parsed_line.kwargs['invoker_name']
        self._check_for_dupe_arenas(invoker_dbref)
        arena_name = "%s's arena" % invoker_name
        mux_commands.pemit(p, invoker_dbref, "Creating an arena...")
        arena_master_dbref, staging_dbref = yield create_arena(
            p, arena_name, invoker_dbref)
        mux_commands.pemit(p, invoker_dbref, "Arena ready: %s" % arena_master_dbref)

        think_fn_wrappers.tel(p, invoker_dbref, staging_dbref)

    def _check_for_dupe_arenas(self, invoker_dbref):
        puppets = PUPPET_STORE.list_all_puppets()
        for puppet in puppets:
            if puppet.creator_dbref == invoker_dbref:
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
        mux_commands.pemit(p, invoker_dbref, "Destroying arena: %s" % arena_master_dbref)
        try:
            PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError("Invalid arena dbref.")

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

        puppets = PUPPET_STORE.list_all_puppets()

        retval = self._get_header_str('Active Arena Listing')
        retval += self._get_footer_str('-')
        retval += (
            '%ch [rjust(ID,4)]%b [ljust(Arena Name, 40)] '
            '[ljust(Players,10)] '
            'State%cn'
        )
        retval += self._get_footer_str('-')
        for puppet in puppets:
            retval += (
                "%r [rjust({dbref}, 4)]%b [ljust({name},43)] "
                "[ljust(words(zwho(#{dbref})),7)] "
                "{state} (Public)".format(
                dbref=puppet.dbref[1:], name=puppet.arena_name,
                state='Staging'))
        if not puppets:
            retval += "[center(There are no active arenas. Create one!,78)]"
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)


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

        creator_dbref = puppet.creator_dbref
        if creator_dbref != invoker_dbref:
            raise CommandError("Only the arena's original creator can do that.")

        if puppet.game_state.lower() != 'in-between':
            raise CommandError("You may only %ch%cgcontinue%cn when between waves.")

        yield puppet.change_state_to_active(p)


class ArenaMasterCommandTable(InboundCommandTable):

    commands = [
        ArenaListCommand,
        ArenaJoinCommand,

        ContinueMatchCommand,

        PickWaveCommand,
        SpawnWaveCommand,
        FixUnitCommand,
        SpawnFixerCommand,

        CreateArenaCommand,
        DestroyArenaCommand,
    ]
