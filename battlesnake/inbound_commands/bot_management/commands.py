"""
These commands are all bot management related.
"""

from twisted.internet import task
from twisted.internet import reactor
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


class BotWaitTestCommand(BaseCommand):
    """
    A command used to test deferred output.
    """

    command_name = "botwaittest"

    @inlineCallbacks
    def run(self, protocol, parsed_line):
        invoker_dbref = parsed_line.invoker_dbref
        delay_secs = int(parsed_line.kwargs['delay'])
        msg = "Response will happen in approximately %d seconds..." % delay_secs
        mux_commands.pemit(protocol, invoker_dbref, msg)
        yield self.delayed_call(protocol, invoker_dbref, delay_secs)

    def delayed_call(self, protocol, invoker_dbref, seconds):
        return task.deferLater(
            reactor, seconds, self.pemit_response, protocol, invoker_dbref)

    def pemit_response(self, protocol, invoker_dbref):
        mux_commands.pemit(protocol, invoker_dbref, "Response!")
