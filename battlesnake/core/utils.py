"""
Assorted utility functions that are general purpose enough not to go into
another module.

.. note:: Yu'll want to avoid importing other Battlesnake modules from this
    one, as to avoid circular imports.
"""

import uuid

from battlesnake.core.ansi import remove_ansi_codes


def generate_unique_token():
    """
    Generates a [probably] unique token. This is useful for cycling keys
    and respose monitors.

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
