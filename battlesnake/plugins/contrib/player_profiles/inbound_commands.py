from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands


class PlayerSheetCommand(BaseCommand):
    """
    Shows details about a player.
    """

    command_name = "pp_playersheet"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):

        pval = self._get_header_str('Player Sheet')
        pval += ' Coming soon.'
        pval += self._get_footer_str()
        mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)


class PlayerProfilesCommandTable(InboundCommandTable):

    commands = [
        PlayerSheetCommand,
    ]
