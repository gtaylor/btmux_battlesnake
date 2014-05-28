"""
Arena Master puppets are objects that Battlesnake creates and places in
the observation lounges of each arena. The puppet is used to listen for
map events and to issue orders to the AIs.
"""

from battlesnake.core.utils import is_valid_dbref


class ArenaMasterPuppetStore(object):
    """
    This class is responsible for tracking arena puppets, which serve as the
    eyes and areas of the bot.
    """

    def __init__(self):
        self._puppet_store = {}

    def __iter__(self):
        for puppet in self._puppet_store.values():
            yield puppet

    def update_or_add_puppet(self, puppet):
        """
        If the puppet isn't already in the store, add it. If it is, replace
        it with the given puppet.

        :param ArenaMasterPuppet puppet:
        """

        self._puppet_store[puppet.dbref] = puppet

    def remove_puppet_by_dbref(self, puppet_dbref):
        """
        Removes a puppet from the store.

        :raises: KeyError if invalid puppet specified.
        """

        assert is_valid_dbref(puppet_dbref), "Invalid puppet dbref."
        del self._puppet_store[puppet_dbref]

    @property
    def puppet_count(self):
        """
        :rtype: int
        :returns: The number of puppets in the store.
        """

        return len(self._puppet_store)


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, dbref, map_dbref):
        self.dbref = dbref
        self.map_dbref = map_dbref


# Lame that we have to pollute the global namespace, but whatevs.
PUPPET_STORE = ArenaMasterPuppetStore()
