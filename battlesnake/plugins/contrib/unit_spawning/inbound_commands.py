from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.core.utils import is_valid_dbref
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands.think_fn_wrappers import btdesignex
from battlesnake.plugins.contrib.ai.outbound_commands import start_unit_ai
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


class SpawnUnitCommand(BaseCommand):
    """
    Spawns a unit on a map at the specified location.
    """

    command_name = "spawnunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="spawnunit", description='Spawns a unit on a map.')

        parser.add_argument(
            "--ai", action="store_true", default=False,
            help="Spawn with an AI pilot")
        parser.add_argument(
            "--pilot", type=str,
            help="The pilot's dbref. Sets comtitles/tics.")

        parser.add_argument(
            'unit_ref', type=str,
            help="The unit template ref to spawn")
        parser.add_argument(
            'map_dbref', type=str,
            help="The dbref of the map to spawn to")
        parser.add_argument(
            'faction_dbref', type=str,
            help="The faction dbref the unit belongs to.")
        parser.add_argument(
            'x', type=int,
            help="The X coordinate to spawn to.")
        parser.add_argument(
            'y', type=int,
            help="The Y coordinate to spawn to.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)

        unit_ref = args.unit_ref
        map_dbref = args.map_dbref
        faction = get_faction(args.faction_dbref)
        unit_x = args.x
        unit_y = args.y
        pilot_dbref = args.pilot

        if pilot_dbref:
            assert is_valid_dbref(args.pilot), "Invalid pilot dbref."

        is_valid_ref = yield btdesignex(protocol, unit_ref)
        if not is_valid_ref:
            raise CommandError("Invalid unit reference.")

        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction, unit_x, unit_y,
            pilot_dbref=pilot_dbref)

        pval = "New unit {unit_dbref} spawned.".format(unit_dbref=unit_dbref)
        mux_commands.pemit(protocol, invoker_dbref, pval)

        if args.ai:
            ai_dbref = yield start_unit_ai(protocol, unit_dbref)
            pval = "AI pilot {ai_dbref} is taking control of {unit_dbref}.".format(
                ai_dbref=ai_dbref, unit_dbref=unit_dbref)
            mux_commands.pemit(protocol, invoker_dbref, pval)


class UnitSpawningCommandTable(InboundCommandTable):

    commands = [
        SpawnUnitCommand,
    ]
