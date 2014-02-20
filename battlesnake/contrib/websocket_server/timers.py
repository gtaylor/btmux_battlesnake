from battlesnake.conf import settings
from battlesnake.core.timers import TimerTable, IntervalTimer

from battlesnake.contrib.hudinfo_cache.store import UNIT_STORE
from battlesnake.contrib.websocket_server.signals import unit_store_contents_signal


class UnitStoreBroadcasterTimer(IntervalTimer):
    """
    Broadcasts a serialized copy of the unit store out to all connected
    listeners, which in turn goes to all connected clients.
    """

    interval = settings['websocket_server']['unit_broadcast_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* Unit store broadcaster interval: %ss" % cls.interval

    def run(self, protocol):
        if unit_store_contents_signal.receivers:
            # Only go through the trouble of serializing the unit store if
            # there is someone connected.
            serialized = UNIT_STORE.get_serialized_units()
            unit_store_contents_signal.send(self, serialized=serialized)


class WebSocketServerTimerTable(TimerTable):
    """
    WebSocket server timers.
    """

    timers = [
        UnitStoreBroadcasterTimer,
    ]
