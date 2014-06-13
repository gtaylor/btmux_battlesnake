from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.units.outbound_commands import \
    spawn_wave

from battlesnake.plugins.contrib.arena_master.puppets.units.waves import \
    pick_refs_for_wave


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
    Picks a wave full of units based on the provided conditions.
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


class ArenaMasterCommandTable(InboundCommandTable):

    commands = [
        PickWaveCommand,
        SpawnWaveCommand,
    ]
