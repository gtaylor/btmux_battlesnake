from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.chargen.archetypes import JACK_OF_ALL_TRADES
from battlesnake.plugins.contrib.chargen.outbound_commands import \
    setup_new_player


class SetupNewPlayerCommand(BaseCommand):
    """
    Sets up a new player's skills and other fun stuff.
    """

    command_name = "chargen_setupnewplayer"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        yield mux_commands.pemit(protocol, parsed_line.invoker_dbref,
            "Starting new player setup...")

        sendto_dbref = parsed_line.kwargs['sendto_dbref']
        yield setup_new_player(
            protocol, invoker_dbref, JACK_OF_ALL_TRADES, sendto_dbref)

        yield mux_commands.pemit(protocol, parsed_line.invoker_dbref,
            "New player setup complete! You'll want to add the default macro set "
            "by typing: %ch%cg.add 0%cn")


class ChargenCommandTable(InboundCommandTable):

    commands = [
        SetupNewPlayerCommand,
    ]
