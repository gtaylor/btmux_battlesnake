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

    trigger_str = "botinfo"

    @inlineCallbacks
    def run(self, protocol, parsed_line):
        invoker_dbref = parsed_line.invoker_dbref
        bot_dbref = yield mux_commands.think(protocol, "%#")
        bot_name = yield mux_commands.think(protocol, "[name(%#)]")
        pval = (
            "============ Battlesnake Botinfo ============\r"
            " Bot name: {bot_name}\r"
            " Bot DBref: {bot_dbref}\r"
            "============================================="
        ).format(
            bot_name=bot_name,
            bot_dbref=bot_dbref
        )
        mux_commands.pemit(protocol, invoker_dbref, pval)
