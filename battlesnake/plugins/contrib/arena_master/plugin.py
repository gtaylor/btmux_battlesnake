from twisted.internet.defer import inlineCallbacks

from battlesnake.core.base_plugin import BattlesnakePlugin
from battlesnake.plugins.contrib.arena_master.puppets.outbound_commands import \
    populate_puppet_store


class ArenaMasterPlugin(BattlesnakePlugin):
    """
    Central tie-in point for the arena master.
    """

    @inlineCallbacks
    def do_after_plugin_is_loaded(self):
        yield populate_puppet_store(self.protocol)
