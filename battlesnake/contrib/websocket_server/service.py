from twisted.application import internet
from autobahn.wamp1.protocol import WampServerFactory

from battlesnake.conf import settings
from battlesnake.contrib.websocket_server.protocol import HexMapWampServerProtocol


def get_websocket_service():
    """
    Instantiates an appropriate service instance for the websocket service.

    :returns: The TCP Server based websocket service.
    """

    bind_uri = settings['websocket_server']['bind_uri']
    port = settings['websocket_server']['port']
    factory = WampServerFactory(bind_uri, debugWamp=False)
    factory.protocol = HexMapWampServerProtocol
    # noinspection PyUnresolvedReferences
    return internet.TCPServer(port, factory)
