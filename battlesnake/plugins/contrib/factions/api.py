"""
Front-facing APIs for faction management.

.. note:: For now, a lot of this is hardcoded for the sake of getting things
    rolling. Eventually this will be DB-backed.
"""

from battlesnake.core.utils import is_valid_dbref

from battlesnake.plugins.contrib.factions.defines import FACTIONS


def is_valid_faction_dbref(dbref):
    """
    :param str dbref: The dbref of a faction object.
    :rtype: bool
    :returns: True if the given dbref is a valid faction object.
    """

    if not is_valid_dbref(dbref):
        return False

    if dbref not in FACTIONS:
        return False

    return True


def get_faction(dbref):
    """
    :param str dbref: The dbref of a faction object.
    :rtype: Faction
    :returns: A Faction instance.
    :raises: AssertionError if input is invalid.
    """

    assert is_valid_faction_dbref(dbref), "Invalid faction dbref"
    return FACTIONS.get(dbref)


def get_faction_list():
    """
    :rtype: list
    :returns: A list of Faction instances.
    """

    return FACTIONS.values()
