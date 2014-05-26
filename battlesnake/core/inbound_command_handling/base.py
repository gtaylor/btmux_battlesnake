"""
Contains base command classes for the other modules in this submodule to use.
"""

from battlesnake.core.ansi import ANSI_HI_YELLOW, ANSI_HI_BLUE, ANSI_HI_WHITE, \
    ANSI_NORMAL
from battlesnake.core.utils import remove_all_percent_sequences


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

    def _get_header_str(self, header_text, header_text_color=ANSI_HI_YELLOW,
                        pad_char='=', pad_color=ANSI_HI_BLUE, width=79):
        """
        Forms and returns a standardized header string.

        :param header_text: The text to show in the header
            block.
        :param pad_char: The character to use to pad the header outside the
            header text block.
        :param pad_color: The ANSI sequence to apply to the padding.
        :rtype: str
        """

        buf = pad_color + (pad_char * 3) + ANSI_HI_WHITE
        buf += '%[{header_text_color}{header_text}{color_hi_white}%]{pad_color}'.format(
            header_text_color=header_text_color, header_text=header_text,
            color_hi_white=ANSI_HI_WHITE, pad_color=pad_color,
        )
        # Unfortunately, we have to account for the color escapes in this.
        # If you add or remove %-escapes, adjust this number.
        remaining = width - len(remove_all_percent_sequences(buf))
        buf += pad_char * remaining
        return '\n' + buf + ANSI_NORMAL

    def _get_subheader_str(self, *args, **kwargs):
        """
        Forms and returns a standardized subheader string.
        See :py:meth:`_get_header_str` for signature.

        :rtype: str
        """

        kwargs['pad_char'] = '-'
        return self._get_header_str(*args, **kwargs)

    def _get_footer_str(self, pad_char='=', pad_color=ANSI_HI_BLUE, width=79):
        """
        Forms and returns a standardized footer string.

        :param pad_char: The character to use to form the footer.
        :param pad_color: The ANSI sequence to apply to the padding.
        :rtype: str
        """

        return '\n' + pad_color + (pad_char * width) + ANSI_NORMAL


class CommandError(Exception):
    """
    Raised to provide a generic way to abort a command with an error.
    """

    def __init__(self, message):
        Exception.__init__(self, message)
