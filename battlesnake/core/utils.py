"""
Assorted utility functions that are general purpose enough not to go into
another module.

.. note:: Yu'll want to avoid importing other Battlesnake modules from this
    one, as to avoid circular imports.
"""

import uuid


def generate_unique_token():
    """
    Generates a [probably] unique token. This is useful for cycling keys
    and respose monitors.

    :rtype: str
    :returns: A unique token.
    """

    return uuid.uuid4().hex