"""
Assorted utility functions that are general purpose enough not to go into
another module.

.. note:: Yu'll want to avoid importing other Battlesnake modules from this
    one, as to avoid circular imports.
"""

import uuid
import math

from battlesnake.core.ansi import remove_ansi_codes


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
