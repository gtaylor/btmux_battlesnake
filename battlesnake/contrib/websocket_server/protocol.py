import blinker
from autobahn.wamp1.protocol import WampServerProtocol

from battlesnake.contrib.hudinfo_cache.signals import on_new_unit_detected, \
    on_unit_destroyed, on_stale_unit_removed
from battlesnake.contrib.hudinfo_cache.store import UNIT_STORE


# noinspection PyPep8Naming
class HexMapWampServerProtocol(WampServerProtocol):
    """
    This protocol communicates via WebSockets + WAMP to all connected HexMap
    clients. We send unit locations and events like new units or
    destroyed units.
    """

    def __init__(self):
        # This maps various blinker signals to receivers and WAMP topics.
        self.signals = {
            'on_new_unit_detected': {
                'signal': on_new_unit_detected,
                'topic': 'http://hexmap.com/unit/events/detected',
                'receiver': self._recv_on_new_unit_detected,
            },
            'on_unit_destroyed': {
                'signal': on_unit_destroyed,
                'topic': 'http://hexmap.com/unit/events/destroyed',
                'receiver': self._recv_on_unit_destroyed,
            },
            'on_stale_unit_removed': {
                'signal': on_stale_unit_removed,
                'topic': 'http://hexmap.com/unit/events/stale-removal',
                'receiver': self._recv_on_unit_destroyed,
            }
        }

    def onSessionOpen(self):
        print "Connection opened!", self
        # Create PubSub topics, register RPC methods.
        self._setup_wamp_registrations()
        self._connect_signals()

    def connectionLost(self, reason):
        print "Connection lost.", self, reason
        self._disconnect_signals()
        WampServerProtocol.connectionLost(self, reason)

    def _setup_wamp_registrations(self):
        """
        Registers PubSub topics and RPC methods.
        """

        for signal_dict in self.signals.values():
            self.registerForPubSub(signal_dict['topic'])

        self.registerMethodForRpc(
            "http://hexmap.com/unit-store#get",
            self, HexMapWampServerProtocol._rpc_get_serialized_unit_store)

    def _connect_signals(self):
        """
        Connects the various blinker signals to their receivers on here.
        These signals get translated into PubSub broadcasts.
        """

        for signal_dict in self.signals.values():
            signal_dict['signal'].connect(signal_dict['receiver'])

    def _disconnect_signals(self):
        """
        When a client disconnects, we have to disconnect the signals to
        avoid memory leakage.
        """

        for signal_dict in self.signals.values():
            signal_dict['signal'].disconnect(signal_dict['receiver'])

    # noinspection PyUnusedLocal
    def _recv_on_new_unit_detected(self, sender, unit, unit_serialized):
        """
        :param MapUnit unit:
        :param dict unit_serialized:
        """

        topic = self.signals['on_new_unit_detected']['topic']
        """:type: str"""
        self.dispatch(topic,
            {
                "unit": unit_serialized,
            }
        )

    # noinspection PyUnusedLocal
    def _recv_on_unit_destroyed(self, sender, victim_id, killer_id):
        """
        :param str victim_id:
        :param str killer_id:
        """

        topic = self.signals['on_unit_destroyed']['topic']
        """:type: str"""
        self.dispatch(topic,
            {
                "victim_id": victim_id,
                "killer_id": killer_id,
            }
        )

    # noinspection PyUnusedLocal
    def _recv_on_stale_unit_removed(self, sender, unit):
        """
        :param MapUnit unit:
        """

        topic = self.signals['on_stale_unit_removed']['topic']
        """:type: str"""
        self.dispatch(topic,
            {
                "unit_id": unit.contact_id,
            }
        )

    def _rpc_get_serialized_unit_store(self):
        """
        Retrieves the entire contents of the unit store as JSON.
        """

        return UNIT_STORE.get_serialized_units()
