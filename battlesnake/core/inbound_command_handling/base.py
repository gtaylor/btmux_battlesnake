"""
Contains base command classes for the other modules in this submodule to use.
"""


class BaseCommand(object):
    """
    A basic command class which all/most commands may inherit. Do not instantiate
    this class directly.
    """

    # This is the command string that will cause the line reader to delegate
    # parsing to the child sub-class.
    command_name = None

    def run(self, protocol, parsed_line, invoker_dbref):
        """
        Given the full parsed input from the command line, do some work.
        This can be a deferred in your sub-class.

        :param BattlesnakeTelnetProtocol protocol: A reference back to the
            top level telnet protocol instance.
        :param ParsedInboundCommandLine parsed_line: The parsed line.
        :param str invoker_dbref: The DBRef of the invoking player.
        """

        raise NotImplementedError("Override this method on your sub-class.")


class CommandError(Exception):
    """
    Raised to provide a generic way to abort a command with an error.
    """

    def __init__(self, message):
        Exception.__init__(self, message)
