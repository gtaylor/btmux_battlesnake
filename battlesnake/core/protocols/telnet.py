from twisted.conch.telnet import StatefulTelnetProtocol
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.command_parser import parse_line
from battlesnake.core.inbound_command_handling.command_table import InboundCommandTable
from battlesnake.inbound_commands.bot_management import BotInfoCommand
from battlesnake.outbound_commands import mux_commands
from battlesnake.core.response_watcher import ResponseMonitorManager


# noinspection PyClassHasNoInit,PyClassHasNoInit,PyClassicStyleClass
class BattlesnakeTelnetProtocol(StatefulTelnetProtocol):
    """
    This is a stateful telnet protocol that is used to connect, listen to,
    and send lines to the game. There are a few different states:

    * Discard - Twisted's default, before we connect. Does nothing.
    * login_prompt - We switch to this after connecting. At this point, the
        protocol is looking for a trigger string to let us know to send
        login credentials.
    * authenticate - We've sent our credentials, now it's time to listen to
        see if we end up logged in.
    * monitoring - If authentication was successful, we switch to a monitoring
        state, which is the default active state.

    A few other misc notes:

    * Loss of connection results in the stopping of this application. The
      process supervisor is left to restart it.
    """

    def connectionMade(self):
        print "Connection established."
        # Start looking for a trigger string on the connection banner to
        # tip us off to authenticate.
        self.state = 'login_prompt'

    # noinspection PyUnresolvedReferences
    def connectionLost(self, reason):
        print "Connection lost."
        StatefulTelnetProtocol.connectionLost(self, reason)
        if reactor.running:
            reactor.stop()

    def write(self, line):
        """
        Sends a line of text to the MUX.

        :param string line: The command to send.
        """

        return self.sendLine(line)

    def _start_keepalive_loop(self):
        """
        If the bot is being ran from an external server, we use the IDLE
        command on a loop to make sure that the connection doesn't drop
        unexpectedly.
        """

        def keepalive(protocol):
            mux_commands.idle(protocol)
        lc = LoopingCall(keepalive, self)
        loop_interval = float(settings.get('bot', 'keepalive_interval'))
        if loop_interval:
            print "* Keepalive interval: %ss" % loop_interval
            lc.start(loop_interval)

    def expect(self, regex_str, timeout_secs=3.0, return_regex_group=None):
        """
        Causes the client to start watching for output from the MUX that
        matches the regex in ``regex_str``. We'll wait as long as ``timeout_secs``
        for the match to be found.

        If a match is found, the deferred will be called back with a return
        value of a re.MatchGroup. If ``return_regex_group`` is present, a
        string containing the value of the named regex group will be returned
        instead. This is an optional shortcut for retrieving simple values.

        :param basestring regex_str: A regular expression string to match against.
        :keyword float timeout_secs: How many seconds to wait.
        :keyword basestring return_regex_group: If specified, the Deferred will
            be callback'd with the string value of the requested regex group.
            If this is a None value, the whole re.MatchGroup is returned instead.
        :rtype: defer.Deferred
        """

        return self.response_monitor.monitor(
            regex_str, timeout_secs=timeout_secs, return_regex_group=return_regex_group)

    #
    ## State-specific line handlers. See class docstring for specifics.

    # noinspection PyAttributeOutsideInit
    def telnet_login_prompt(self, line):
        if 'QUIT' in line:
            # Found the trigger phase. Change state and send credentials.
            self.state = 'authenticate'
            bot_username = settings.get('account', 'username')
            bot_password = settings.get('account', 'password')
            self.write('connect "%s" %s' % (bot_username, bot_password))

    def telnet_authenticate(self, line):
        if 'Connected.' in line:
            # Authentication was successful, go active.
            mux_commands.set_attr(
                protocol=self, obj='me', name='BATTLESNAKE_PREFIX.D',
                value=self.cmd_prefix)
            mux_commands.set_attr(
                protocol=self, obj='me', name='BATTLESNAKE_KWARG_DELIMITER.D',
                value=self.cmd_kwarg_delimiter)
            mux_commands.set_attr(
                protocol=self, obj='me', name='BATTLESNAKE_LIST_DELIMITER.D',
                value=self.cmd_kwarg_list_delimiter)
            self._start_keepalive_loop()
            self.response_monitor.start_expiration_loop()
            self.state = 'monitoring'
        elif 'or has a different password.' in line:
            # Invalid username/password. Poop out.
            print "Failure to authenticate."
            # noinspection PyUnresolvedReferences
            reactor.stop()

    def telnet_monitoring(self, line):
        if self.response_monitor.match_line(line):
            return
        parsed_line = parse_line(
            line, self.cmd_prefix, self.cmd_kwarg_delimiter,
            self.cmd_kwarg_list_delimiter)
        if not parsed_line:
            return
        matched_command = self.command_table.match_inbound_command(parsed_line)
        if not matched_command:
            return
        matched_command().run(self, parsed_line)


# noinspection PyAttributeOutsideInit,PyClassHasNoInit,PyClassicStyleClass
class BattlesnakeTelnetFactory(ClientFactory):
    """
    Bullshit enterprisey factory class. Java all the things.
    """

    protocol = BattlesnakeTelnetProtocol

    def buildProtocol(self, addr):
        protocol = self.protocol()
        protocol.factory = self
        protocol.response_monitor = ResponseMonitorManager()

        self._set_dynamic_attribs(protocol)
        self._register_commands(protocol)
        return protocol

    def _set_dynamic_attribs(self, protocol):
        # TODO: Set these dynamically.
        protocol.cmd_prefix = "@G$>"
        protocol.cmd_kwarg_delimiter = "&R^"
        protocol.cmd_kwarg_list_delimiter = "#E$"

    def _register_commands(self, protocol):
        protocol.command_table = InboundCommandTable()
        # TODO: Un-hardcode this.
        commands = [
            BotInfoCommand,
        ]
        for command in commands:
            protocol.command_table.register_command(command)
