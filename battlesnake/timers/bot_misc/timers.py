from battlesnake.core.timers import IntervalTimer
from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands


class IdleTimer(IntervalTimer):
    """
    Periodically sends an IDLE command to make sure that we don't get booted
    off by poorly configured NATs.
    """

    interval = settings['bot']['keepalive_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* Keepalive interval: %ss" % cls.interval

    def run(self, protocol):
        mux_commands.idle(protocol)
