"""
Arena Master puppets are objects that Battlesnake creates and places in
the observation lounges of each arena. The puppet is used to listen for
map events and to issue orders to the AIs.
"""

from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.core.utils import is_valid_dbref
from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions, \
    get
from battlesnake.plugins.contrib.arena_master.puppets.puppet import \
    ArenaMasterPuppet


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

    @property
    def puppet_count(self):
        """
        :rtype: int
        :returns: The number of puppets in the store.
        """

        return len(self._puppet_store)

    def list_arena_master_puppets(self, game_mode=None):
        """
        :keyword str game_mode: Only return puppets of the given game mode.
        :rtype: list
        :returns: A list of all ArenaMasterPuppet instances that we currently
            know about.
        """

        if game_mode:
            return [puppet for puppet in self._puppet_store.values()
                    if puppet.game_mode == game_mode]
        else:
            return self._puppet_store.values()

    @inlineCallbacks
    def add_puppet_from_arena_master_object(self, protocol, arena_master_dbref):
        """
        Calls into the game to get the details needed to instantiate an
        ArenaMasterPuppet instance.

        :param BattlesnakeTelnetProtocol protocol:
        :rtype: defer.Deferred
        :returns: A Deferred whose callback value will be a newly instantiated
            ArenaMasterPuppet instance.
        """

        p = protocol
        map_dbref = yield get(p, arena_master_dbref, 'MAP.DBREF')
        creator_dbref = yield get(p, arena_master_dbref, 'CREATOR.DBREF')
        staging_dbref = yield get(p, arena_master_dbref, 'STAGING_ROOM.DBREF')
        arena_name = yield get(p, arena_master_dbref, 'ARENA_NAME.D')
        current_wave = yield get(p, arena_master_dbref, 'CURRENT_WAVE.D')
        game_mode = yield get(p, arena_master_dbref, 'GAME_MODE.D')
        game_state = yield get(p, arena_master_dbref, 'GAME_STATE.D')
        difficulty_mod = yield get(p, arena_master_dbref, 'DIFFICULTY_MOD.D')
        map_width, map_height = yield get_map_dimensions(p, map_dbref)
        puppet = ArenaMasterPuppet(
            protocol, arena_master_dbref, map_dbref, staging_dbref,
            creator_dbref, map_height, map_width, arena_name, current_wave,
            game_mode, game_state, difficulty_mod)
        self.update_or_add_puppet(puppet)

        returnValue(puppet)

    def get_puppet_by_dbref(self, puppet_dbref):
        """
        :param str puppet_dbref: The dbref of the puppet to get.
        :rtype: ArenaMasterPuppet
        :raises: KeyError when encountering an invalid puppet dbref.
        """

        return self._puppet_store[puppet_dbref]

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

    def find_puppet_for_unit_dbref(self, unit_dbref):
        """
        Find which puppet contains the given unit dbref.

        :param str unit_dbref: The unit whose puppet to find.
        :rtype: ArenaMasterPuppet or None
        """

        for puppet in self.list_arena_master_puppets():
            try:
                puppet.unit_store.get_unit_by_dbref(unit_dbref)
                return puppet
            except ValueError:
                continue


# Lame that we have to pollute the global namespace, but whatevs.
PUPPET_STORE = ArenaMasterPuppetStore()
