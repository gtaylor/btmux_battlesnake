from twisted.application import internet
from autobahn.twisted.websocket import WebSocketServerFactory

from battlesnake.conf import settings
from battlesnake.contrib.websocket_server.protocol import BSWebSocketServerProtocol


def get_websocket_service():
    """
    Instantiates an appropriate service instance for the websocket service.

    :returns: The TCP Server based websocket service.
    """

    bind_uri = settings['websocket_server']['bind_uri']
    port = settings['websocket_server']['port']
    factory = WebSocketServerFactory(bind_uri, debug=False)
    factory.protocol = BSWebSocketServerProtocol
    # noinspection PyUnresolvedReferences
    return internet.TCPServer(port, factory)
