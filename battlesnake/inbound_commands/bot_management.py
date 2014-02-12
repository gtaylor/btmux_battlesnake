"""
These commands are all bot management related.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.outbound_commands import mux_commands


class BotInfoCommand(BaseCommand):
    """
    Shows some assorted info about the bot.
    """

    command_name = "botinfo"

    @inlineCallbacks
    def run(self, protocol, parsed_line):
        invoker_dbref = parsed_line.invoker_dbref
        bot_dbref = yield mux_commands.think(protocol, "%#")
        bot_name = yield mux_commands.think(protocol, "[name(%#)]")
        pval = (
            "============ Battlesnake Botinfo ============\r"
            " Bot name: {bot_name}\r"
            " Bot DBref: {bot_dbref}\r"
            " Command Prefix: {cmd_prefix}\r"
            " Command Kwarg Delim: {cmd_kwarg_delimiter}\r"
            " Command Kwarg List Delim: {cmd_kwarg_list_delimiter}\r"
            "============================================="
        ).format(
            bot_name=bot_name,
            bot_dbref=bot_dbref,
            cmd_prefix=protocol.cmd_prefix,
            cmd_kwarg_delimiter=protocol.cmd_kwarg_delimiter,
            cmd_kwarg_list_delimiter=protocol.cmd_kwarg_list_delimiter,
        )
        mux_commands.pemit(protocol, invoker_dbref, pval)
