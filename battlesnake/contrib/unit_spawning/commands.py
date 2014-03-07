from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.contrib.unit_spawning.outbound_commands.unit_creation import \
    create_unit


class SpawnUnitCommand(BaseCommand):
    """
    Spawns a unit on a map at the specified location.
    """

    command_name = "spawnunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line):
        if not parsed_line.kwargs:
            self.handle_noargs(protocol, parsed_line)
            return

        unit_ref = parsed_line.kwargs['ref']
        map_dbref = parsed_line.kwargs['map_dbref']
        # TODO: Do something with this.
        faction_alias = parsed_line.kwargs['faction_alias']
        faction_name = "Admin"
        unit_x = parsed_line.kwargs['x']
        unit_y = parsed_line.kwargs['y']
        # TODO: Un-hardcode.
        team_num = 1

        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction_name, team_num, unit_x, unit_y)

        pval = "New unit {unit_dbref}".format(unit_dbref=unit_dbref)
        mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)

    def handle_noargs(self, protocol, parsed_line):
        """
        No arguments passed to the command. Show a brief cheat sheet.
        """

        pval = (
            "%chspawnunit%cn <unit_ref>=<map_dbref>,<faction_alias>,<x>,<y>"
        )
        mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)
