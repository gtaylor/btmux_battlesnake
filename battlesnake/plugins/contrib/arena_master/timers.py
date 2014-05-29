from battlesnake.conf import settings
from battlesnake.core.timers import IntervalTimer
from battlesnake.core.timers import TimerTable

from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE


class StrategyTicTimer(IntervalTimer):
    """
    Looks through all of the AIs being watched by each puppet and makes
    decisions on what to do.
    """

    interval = settings['arena_master']['arena_master_puppet_strategic_tic_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* Arena master puppet strategic tic interval: %ss" % cls.interval

    def run(self, protocol):
        for puppet in PUPPET_STORE:
            puppet.do_strategic_tic()


class ArenaPuppetMasterTimerTable(TimerTable):
    """
    Misc. core bot timers.
    """

    timers = [
        StrategyTicTimer,
    ]
