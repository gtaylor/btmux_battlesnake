from twisted.internet.defer import inlineCallbacks

from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.arena_master.puppets.units.outbound_commands import \
    populate_puppet_store
from battlesnake.plugins.contrib.arena_master.puppets.units.timers import \
    ArenaPuppetMasterUnitStoreTimerTable
from battlesnake.plugins.contrib.arena_master.timers import \
    ArenaPuppetMasterTimerTable


class ArenaMasterPlugin(BattlesnakePlugin):
    """
    Central tie-in point for the arena master.
    """

    timer_tables = [
        ArenaPuppetMasterUnitStoreTimerTable,
        ArenaPuppetMasterTimerTable,
    ]

    @inlineCallbacks
    def do_after_plugin_is_loaded(self):
        yield populate_puppet_store(self.protocol)
