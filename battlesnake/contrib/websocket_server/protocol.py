import blinker
from autobahn.wamp1.protocol import WampServerProtocol


# noinspection PyPep8Naming
class HexMapWampServerProtocol(WampServerProtocol):
    """
    This protocol communicates via WebSockets + WAMP to all connected HexMap
    clients. We send unit locations and events like new units or
    destroyed units.
    """

    def __init__(self):
        self.unit_store_contents_signal = None

    def onSessionOpen(self):
        print "Connection opened!", self
        self.registerForPubSub("http://example.com/myEvent1")

        self.unit_store_contents_signal = blinker.signal('unit_store_contents_signal')
        # A timer sends unit data over this signal periodically, which gets
        # pushed out to all connected clients.
        self.unit_store_contents_signal.connect(self._unit_store_contents_signal_receiver)

    def connectionLost(self, reason):
        print "Connection lost.", self, reason
        self.unit_store_contents_signal.disconnect(self._unit_store_contents_signal_receiver)
        WampServerProtocol.connectionLost(self, reason)

    # noinspection PyUnusedLocal
    def _unit_store_contents_signal_receiver(self, sender, serialized):
        """
        A timer sends a serialized representation of the unit store every
        so often. This receiver is where the data ends up. Each connected
        client gets a copy of the data.
        """

        self.dispatch("http://example.com/myEvent1",
            {
                "units": serialized,
            }
        )
