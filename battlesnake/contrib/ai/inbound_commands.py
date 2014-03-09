from twisted.internet.defer import inlineCallbacks
from battlesnake.contrib.ai.outbound_commands import start_unit_ai

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands


class StartUnitAICommand(BaseCommand):
    """
    Spawns a unit on a map at the specified location.
    """

    command_name = "startunitai"

    @inlineCallbacks
    def run(self, protocol, parsed_line):
        if not parsed_line.kwargs:
            self.handle_noargs(protocol, parsed_line)
            return

        unit_dbref = parsed_line.kwargs['unit_dbref']
        ai_dbref = yield start_unit_ai(protocol, unit_dbref)

        pval = "AI activated AI {ai_dbref} on {unit_dbref}.".format(
            ai_dbref=ai_dbref, unit_dbref=unit_dbref)
        mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)

    def handle_noargs(self, protocol, parsed_line):
        """
        No arguments passed to the command. Show a brief cheat sheet.
        """

        pval = (
            "%startunitai%cn <unit_dbref>"
        )
        mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)


class AICommandTable(InboundCommandTable):

    commands = [
        StartUnitAICommand,
    ]
