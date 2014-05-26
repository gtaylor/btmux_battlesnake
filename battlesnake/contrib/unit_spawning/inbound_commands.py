from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.contrib.unit_spawning.outbound_commands import \
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
        yield self.handle(protocol, invoker_dbref, args)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)

        unit_ref = args.unit_ref
        map_dbref = args.map_dbref
        # TODO: Do something with this.
        faction_alias = args.faction_dbref
        faction_name = "Admin"
        unit_x = args.x
        unit_y = args.y
        # TODO: Un-hardcode.
        team_num = 1

        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction_name, team_num, unit_x, unit_y)

        pval = "New unit {unit_dbref} spawned.".format(unit_dbref=unit_dbref)
        mux_commands.pemit(protocol, invoker_dbref, pval)


class UnitSpawningCommandTable(InboundCommandTable):

    commands = [
        SpawnUnitCommand,
    ]
