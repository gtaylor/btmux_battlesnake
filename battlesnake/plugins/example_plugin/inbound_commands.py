"""
These commands are all bot management related.
"""

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.command_table import InboundCommandTable
from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.outbound_commands import mux_commands


class BotInfoCommand(BaseCommand):
    """
    Shows some assorted info about the bot.
    """

    command_name = "botinfo"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        bot_dbref = yield mux_commands.think(protocol, "%#")
        bot_name = yield mux_commands.think(protocol, "[name(%#)]")
        pval = self._get_header_str("Battlesnake Botinfo", width=50)
        pval += (
            "\r"
            " Bot name: {bot_name}\r"
            " Bot DBref: {bot_dbref}\r"
            " Command Prefix: {cmd_prefix}\r"
            " Command Kwarg Delim: {cmd_kwarg_delimiter}\r"
            " Command Kwarg List Delim: {cmd_kwarg_list_delimiter}"
        ).format(
            bot_name=bot_name,
            bot_dbref=bot_dbref,
            cmd_prefix=protocol.cmd_prefix,
            cmd_kwarg_delimiter=protocol.cmd_kwarg_delimiter,
            cmd_kwarg_list_delimiter=protocol.cmd_kwarg_list_delimiter,
        )
        pval += self._get_footer_str(width=50)
        mux_commands.pemit(protocol, invoker_dbref, pval)


class BotWaitTestCommand(BaseCommand):
    """
    A command used to test deferred output.
    """

    command_name = "botwaittest"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        delay_secs = int(parsed_line.kwargs['delay'])
        msg = "Response will happen in approximately %d seconds..." % delay_secs
        mux_commands.pemit(protocol, invoker_dbref, msg)
        yield self.delayed_call(protocol, invoker_dbref, delay_secs)

    def delayed_call(self, protocol, invoker_dbref, seconds):
        return task.deferLater(
            reactor, seconds, self.pemit_response, protocol, invoker_dbref)

    def pemit_response(self, protocol, invoker_dbref):
        mux_commands.pemit(protocol, invoker_dbref, "Response!")


class CliffTestCommand(BaseCommand):
    """
    Tests the Python cliff CLI module integration.
    """

    command_name = "clifftest"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        import inspect
        mux_commands.pemit(protocol, invoker_dbref, "YAR")
        yield protocol.expect(r'^test', debug_info=inspect.stack(), timeout_secs=1.0)


class ExampleCommandTable(InboundCommandTable):
    """
    Command table for bot management commands.
    """

    commands = [
        BotInfoCommand,
        BotWaitTestCommand,
        CliffTestCommand,
    ]
