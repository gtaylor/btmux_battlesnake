"""
Assorted utility functions that are general purpose enough not to go into
another module.

.. note:: Yu'll want to avoid importing other Battlesnake modules from this
    one, as to avoid circular imports.
"""

import uuid
import math

from battlesnake.core.ansi import remove_ansi_codes, ANSI_HI_YELLOW, \
    ANSI_HI_BLUE, ANSI_NORMAL, ANSI_HI_WHITE


def calc_range(x1, y1, z1, x2, y2, z2):
    """
    Finds the range between two sets of x/y coords.

    :param float x1:
    :param float y1:
    :param float z1:
    :param float x2:
    :param float y2:
    :param float z2:
    :rtype: float
    :returns: The range between the two coordinates.
    """

    dx = float(x1) - x2
    dy = float(y1) - y2
    dz = float(z1) - z2
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def calc_xy_range(x1, y1, x2, y2):
    """
    Finds the range between two sets of x/y coords.

    :param float x1:
    :param float y1:
    :param float x2:
    :param float y2:
    :rtype: float
    :returns: The range between the two coordinates.
    """

    dx = float(x1) - x2
    dy = float(y1) - y2
    return math.sqrt(dx * dx + dy * dy)


def generate_unique_token():
    """
    Generates a [probably] unique token. This is useful for cycling keys
    and response monitors.

    :rtype: str
    :returns: A unique token.
    """

    return uuid.uuid4().hex


def is_valid_dbref(dbref):
    """
    :param str dbref: The DBRef string to validate.
    :rtype: bool
    :returns: True if the given string is a valid dbref, False if not.
    """

    if not isinstance(dbref, basestring):
        return False

    # noinspection PyUnresolvedReferences
    if not dbref.startswith('#'):
        return False

    if dbref == '#-1':
        return False

    # noinspection PyUnresolvedReferences
    if not dbref[1:].isdigit():
        return False

    return True


def remove_all_percent_sequences(text):
    """
    Given a string, remove all %-sequences. This includes color codes,
    escaped parenthesis, spaces, tabs, etc.
    """

    text = text.replace('%b', ' ')
    text = text.replace('%t', '\t')
    text = text.replace('%r', '\r')
    text = text.replace('%(', '(')
    text = text.replace('%)', ')')
    text = text.replace('%[', '[')
    text = text.replace('%]', ']')
    text = text.replace('%%', '%')
    text = remove_ansi_codes(text)
    return text


def add_escaping_percent_sequences(text):
    """
    Given a string, add %-escapes to all characters needing them in order
    to allow passing a literal value.
    """

    text = text.replace('%', '%%')
    text = text.replace(' ', '%b')
    text = text.replace('\t', '%t')
    text = text.replace('\r', '%r')
    text = text.replace('(', '%(')
    text = text.replace(')', '%)')
    text = text.replace('[', '%[')
    text = text.replace(']', '%]')
    text = remove_ansi_codes(text)
    return text


def get_header_str(header_text, header_text_color=ANSI_HI_YELLOW,
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


def get_subheader_str(*args, **kwargs):
    """
    Forms and returns a standardized subheader string.
    See :py:func:`get_header_str` for signature.

    :rtype: str
    """

    kwargs['pad_char'] = '-'
    return get_header_str(*args, **kwargs)


def get_footer_str(pad_char='=', pad_color=ANSI_HI_BLUE, width=79):
    """
    Forms and returns a standardized footer string.

    :param pad_char: The character to use to form the footer.
    :param pad_color: The ANSI sequence to apply to the padding.
    :rtype: str
    """

    return '\n' + pad_color + (pad_char * width) + ANSI_NORMAL
