from battlesnake.conf import settings
from battlesnake.contrib.hudinfo_cache.store import UNIT_STORE
from battlesnake.core.timers import TimerTable, IntervalTimer

from battlesnake.outbound_commands import hudinfo_commands


class HudinfoContactPullerTimer(IntervalTimer):
    """
    Periodically sends a 'hudinfo c' to retrieve the latest contact
    data for a map.
    """

    interval = settings['hudinfo_cache']['contact_puller_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* hudinfo_cache contact puller interval: %ss" % cls.interval

    def run(self, protocol):
        hudinfo_commands.hudinfo_contacts(protocol)
        UNIT_STORE.purge_stale_units()


class HudinfoCacheTimerTable(TimerTable):
    """
    hudinfo_cache timers.
    """

    timers = [
        HudinfoContactPullerTimer,
    ]
