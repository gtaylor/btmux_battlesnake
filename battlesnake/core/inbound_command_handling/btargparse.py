"""
An optional set of classes used to shoehorn argparse into inbound commands.
This can be helpful in cases where we'd end up with cumbersome argument
structures in softcode.
"""

import argparse

from battlesnake.outbound_commands import mux_commands


class BTMuxArgumentParserExit(Exception):
    """
    Raised when an error during parsing happens. This replaces the SystemExit
    exception that sys.exit() normally raises.
    """

    def __init__(self, message):
        Exception.__init__(self, message)


class BTMuxArgumentParser(argparse.ArgumentParser):
    """
    Use this ArgumentPaser sub-class instead of ArgumentParser directly.
    """

    def __init__(self, protocol, invoker_dbref, *args, **kwargs):
        self.protocol = protocol
        self.invoker_dbref = invoker_dbref
        super(BTMuxArgumentParser, self).__init__(*args, **kwargs)

    def _print_message(self, message, file=None):
        """
        argparse normally dumps to stdout, but we have to change that
        behavior to make sure the messages get back to the invoker.
        """

        # Escape a few common softcode sequences.
        message = message.replace('[', '%[')
        message = message.replace(']', '%]')
        message = message.replace('(', '%(')
        message = message.replace(')', '%)')
        # Preserves multiple adjacent spaces, which MUX strips.
        message = message.replace(' ', '%b')
        message = '%r' + message
        mux_commands.pemit(self.protocol, self.invoker_dbref, message)

    def exit(self, status=0, message=None):
        """
        argparse normally does a sys.exit here, but we'll raise an exception
        that gets picked up by the BattlesnakeTelnetProtocol.
        """

        raise BTMuxArgumentParserExit(message)
