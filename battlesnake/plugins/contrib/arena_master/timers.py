from battlesnake.conf import settings
from battlesnake.core.timers import IntervalTimer
from battlesnake.core.timers import TimerTable


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
        pass


class ArenaPuppetMasterTimerTable(TimerTable):
    """
    Misc. core bot timers.
    """

    timers = [
        StrategyTicTimer,
    ]
