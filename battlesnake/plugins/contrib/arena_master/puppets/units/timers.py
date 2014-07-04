from battlesnake.conf import settings
from battlesnake.core.timers import TimerTable, IntervalTimer

from battlesnake.plugins.contrib.arena_master.puppets.units.store_populater import \
    update_store_from_btfuncs
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE


class ThinkBTContactPullerTimer(IntervalTimer):
    """
    Periodically iterates over each map's units, populating arena puppet
    unit stores in the process.

    This is currently pretty inefficient. May be a good candidate for
    creating a hardcoded function that wraps all of this up once things settle.
    """

    interval = settings['arena_master']['contact_puller_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* arena_master contact puller interval: %ss" % cls.interval

    def run(self, protocol):
        for arena_puppet in PUPPET_STORE:
            update_store_from_btfuncs(protocol, arena_puppet.unit_store)


class ArenaPuppetMasterUnitStoreTimerTable(TimerTable):

    timers = [
        ThinkBTContactPullerTimer,
    ]
