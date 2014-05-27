from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.factions.api import get_faction_list


class FaclistCommand(BaseCommand):
    """
    Shows a list of factions.
    """

    command_name = "faclist"

    def run(self, protocol, parsed_line, invoker_dbref):
        pval = self._get_header_str("Faction List", width=50)
        for faction in get_faction_list():
            pval += "%r [ljust({faction_dbref},5)] {faction_name}".format(
                faction_dbref=faction.dbref, faction_name=faction.name,
            )
        pval += self._get_footer_str(width=50)
        mux_commands.pemit(protocol, invoker_dbref, pval)


class FactionCommandTable(InboundCommandTable):

    commands = [
        FaclistCommand,
    ]
