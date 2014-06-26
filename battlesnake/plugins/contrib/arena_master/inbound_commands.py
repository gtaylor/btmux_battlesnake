from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.puppets.units.damages_setter import \
    uniformly_repair_armor, fix_all_internals, reload_all_ammo
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import DEFENDER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_library.api import get_unit_by_ref

from battlesnake.plugins.contrib.arena_master.puppets.units.outbound_commands import \
    spawn_wave
from battlesnake.plugins.contrib.arena_master.puppets.units.waves import \
    pick_refs_for_wave
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


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


class SimpleSpawnCommand(BaseCommand):
    """
    A really basic spawn command we can use to test arenas.
    """

    command_name = "am_simplespawn"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        unit_ref = parsed_line.kwargs['unit_ref']
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        unit = yield get_unit_by_ref(unit_ref)
        if not unit:
            raise CommandError('Invalid unit reference!')

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        yield think_fn_wrappers.btsetcharvalue(p, invoker_dbref, 'bruise', 0, 0)
        yield think_fn_wrappers.btsetcharvalue(p, invoker_dbref, 'lethal', 0, 0)

        map_dbref = puppet.map_dbref
        faction = get_faction(DEFENDER_FACTION_DBREF)
        unit_x, unit_y = puppet.get_defender_spawn_coords()

        unit_dbref = yield create_unit(
            p, unit.reference, map_dbref, faction, unit_x, unit_y,
            pilot_dbref=invoker_dbref)
        yield think_fn_wrappers.tel(p, invoker_dbref, unit_dbref)
        yield mux_commands.force(p, invoker_dbref, 'startup')


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


class ArenaMasterCommandTable(InboundCommandTable):

    commands = [
        PickWaveCommand,
        SpawnWaveCommand,
        SimpleSpawnCommand,
        FixUnitCommand,
    ]
