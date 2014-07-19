from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.chargen.archetypes import JACK_OF_ALL_TRADES
from battlesnake.plugins.contrib.chargen.outbound_commands import \
    setup_new_player
from battlesnake.plugins.contrib.player_profiles.api import add_existing_player_to_db


class SetupNewPlayerCommand(BaseCommand):
    """
    Sets up a new player's skills and other fun stuff.
    """

    command_name = "chargen_setupnewplayer"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="register", description='Completes character creation.')

        parser.add_argument(
            'email', type=str,
            help="Your email address.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args, parsed_line)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args, parsed_line):
        email = args.email
        invalid_email_msg = 'Please use a valid email address.'
        if '@' not in email:
            raise CommandError(invalid_email_msg)
        if '.' not in email:
            raise CommandError(invalid_email_msg)

        yield add_existing_player_to_db(
            invoker_dbref, parsed_line.kwargs['username'], email)

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
