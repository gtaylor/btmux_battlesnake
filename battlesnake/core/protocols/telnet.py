from twisted.conch.telnet import StatefulTelnetProtocol
from twisted.internet.defer import inlineCallbacks, maybeDeferred
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.base import CommandError
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import hudinfo_commands
from battlesnake.outbound_commands import mux_commands

from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParserExit
from battlesnake.core.py_importer import import_class
from battlesnake.core.utils import generate_unique_token
from battlesnake.core.response_watcher import ResponseWatcherManager
from battlesnake.core.inbound_command_handling.command_parser import parse_line


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

    def __init__(self, cmd_prefix, cmd_kwarg_delimiter, cmd_kwarg_list_delimiter,
                 command_tables, trigger_tables, timer_tables):
        self.cmd_prefix = cmd_prefix
        self.cmd_kwarg_delimiter = cmd_kwarg_delimiter
        self.cmd_kwarg_list_delimiter = cmd_kwarg_list_delimiter
        self.command_tables = command_tables
        self.trigger_tables = trigger_tables
        self.timer_tables = timer_tables
        self.watcher_manager = ResponseWatcherManager()
        self.hudinfo_enabled = settings['bot']['enable_hudinfo']
        # This is populated once we set a key in-game.
        self.hudinfo_key = None

    def connectionMade(self):
        print "Connection established."
        # Start looking for a trigger string on the connection banner to
        # tip us off to authenticate.
        self.state = 'login_prompt'

    # noinspection PyUnresolvedReferences
    def connectionLost(self, reason):
        print "Connection lost."
        StatefulTelnetProtocol.connectionLost(self, reason)

    def write(self, line):
        """
        Sends a line of text to the MUX.

        :param string line: The command to send.
        """

        self.sendLine(line)

    def write_and_wait(self, line, ack_regex_str=None):
        """
        This is used for commands where we don't necessarily care about the
        output, but we want to make sure that the command completed execution.

        .. warning:: Despite getting a response and triggering the deferred,
            the command may not actually be done yet. This is a pretty
            flimsy way of handling this, but we may be able to figure
            out something better in the future.

        :param string line: The command to send.
        """

        if not ack_regex_str:
            # No acknowledgement regex was specified, so we'll generate a
            # token and run a 'think' after the command.
            postfix_token = generate_unique_token()
            postfix_line = "think " + postfix_token
            regex_str = r'{postfix}\r$'.format(postfix=postfix_token)
            deferred = self.expect(regex_str)
            self.sendLine(postfix_line)
        else:
            postfix_line = None
            deferred = self.expect(ack_regex_str)

        self.sendLine(line)

        if postfix_line:
            self.sendLine(postfix_line)
        return deferred

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

        return self.watcher_manager.watch(
            regex_str, timeout_secs=timeout_secs, return_regex_group=return_regex_group)

    @inlineCallbacks
    def gen_and_set_hudinfo_key(self):
        """
        Generates and sets a HUDINFO key.
        """

        potential_key = generate_unique_token()[:20]
        hudinfo_key = yield hudinfo_commands.hudinfo_set_key(self, potential_key)
        if hudinfo_key:
            self.hudinfo_key = hudinfo_key
            print "* HUDINFO active. Key: %s" % self.hudinfo_key
        else:
            print "Error: Unable to set HUDINFO key %s" % potential_key

    #
    ## State-specific line handlers. See class docstring for specifics.

    # noinspection PyAttributeOutsideInit
    def telnet_login_prompt(self, line):
        if 'QUIT' in line:
            # Found the trigger phase. Change state and send credentials.
            self.state = 'authenticate'
            bot_username = settings['account']['username']
            bot_password = settings['account']['password']
            self.write('connect "%s" %s' % (bot_username, bot_password))

    def telnet_authenticate(self, line):
        if 'Connected.' in line:
            # Authentication was successful, go active.
            botinfo_attribs = {
                'BATTLESNAKE_PREFIX.D': self.cmd_prefix,
                'BATTLESNAKE_KWARG_DELIMITER.D': self.cmd_kwarg_delimiter,
                'BATTLESNAKE_LIST_DELIMITER.D': self.cmd_kwarg_list_delimiter,
            }
            think_fn_wrappers.set_attrs(
                protocol=self, obj='me', attr_dict=botinfo_attribs)
            self.watcher_manager.start_expiration_loop()
            self.state = 'monitoring'
            if self.hudinfo_enabled:
                self.gen_and_set_hudinfo_key()
        elif 'or has a different password.' in line:
            # Invalid username/password. Poop out.
            print "Failure to authenticate."
            # noinspection PyUnresolvedReferences
            reactor.stop()

    def telnet_monitoring(self, line):
        if self.watcher_manager.match_line(line):
            # Something was waiting to get a response value from a command,
            # and we found the match.
            return

        for trigger_table in self.trigger_tables:
            matched_trigger = trigger_table.match_line(line)
            if not matched_trigger:
                continue
            trigger_obj, re_match = matched_trigger
            trigger_obj().run(self, line, re_match)
            return

        # Figure out if this line is an inbound command.
        parsed_line = parse_line(
            line, self.cmd_prefix, self.cmd_kwarg_delimiter,
            self.cmd_kwarg_list_delimiter)
        if not parsed_line:
            # Wasn't a command, go no further.
            return

        # This line was an inbound command.
        for command_table in self.command_tables:
            matched_command = command_table.match_inbound_command(parsed_line)
            if not matched_command:
                continue

            invoker_dbref = parsed_line.invoker_dbref
            command_instance = matched_command()
            # Outbound commands are executed through their run() method. These
            # may or may not return deferreds.
            d = maybeDeferred(
                command_instance.run, self, parsed_line, invoker_dbref)
            d.addErrback(self._command_errback, invoker_dbref)

    def _command_errback(self, err, invoker_dbref):
        """
        Inbound commands may or may not be a deferred, so we have to
        handle exceptions in here.
        """

        # BTMuxArgumentParserExit isn't necessarily an error, just our
        # modified ArgParse doing a fake "exit".
        e = err.trap(BTMuxArgumentParserExit, CommandError)
        if e == CommandError:
            mux_commands.pemit(self, invoker_dbref, str(err.value))


# noinspection PyAttributeOutsideInit,PyClassHasNoInit,PyClassicStyleClass
class BattlesnakeTelnetFactory(ClientFactory):
    """
    Bullshit enterprisey factory class. Java all the things.
    """

    protocol = BattlesnakeTelnetProtocol

    def buildProtocol(self, addr):
        protocol = self.protocol(
            # TODO: Set these dynamically.
            cmd_prefix="@G$>",
            cmd_kwarg_delimiter="&R^",
            cmd_kwarg_list_delimiter="#E$",
            command_tables=self._load_and_return_commands(),
            trigger_tables=self._load_and_return_triggers(),
            # We need the protocol reference to do this.
            timer_tables=None
        )
        # TODO: Maybe there's a better way.
        protocol.timer_tables = self._load_and_return_timers(protocol)
        protocol.factory = self

        return protocol

    def _load_and_return_commands(self):
        """
        Pull the command tables from settings and get them all instantiated
        and registered.
        """

        print "Loading command tables..."
        tables = []
        for table in settings['commands']['inbound_tables']:
            print "  - Loading", table
            table_class = import_class(table)
            tables.append(table_class())
        return tables

    def _load_and_return_triggers(self):
        """
        Pull the trigger tables from settings and get them all instantiated
        and registered.
        """

        print "Loading trigger tables..."
        tables = []
        for table in settings['triggers']['tables']:
            print "  - Loading", table
            table_class = import_class(table)
            tables.append(table_class())
        return tables

    def _load_and_return_timers(self, protocol):
        """
        Pull the timer tables from settings and get them all instantiated
        and registered.
        """

        print "Loading timer tables..."
        tables = []
        for table in settings['timers']['tables']:
            print "  - Loading", table
            table_class = import_class(table)
            tables.append(table_class(protocol))
        return tables
