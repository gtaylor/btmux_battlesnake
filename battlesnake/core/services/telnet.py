from twisted.application import internet

from battlesnake.conf import settings
from battlesnake.core.protocols.telnet import BattlesnakeTelnetFactory


def get_telnet_service():
    """
    Instantiates an appropriate service instance for the telnet client.

    :returns: The TCPClient based Telnet service.
    """

    hostname = settings['mux']['hostname']
    port = settings['mux']['port']
    # noinspection PyUnresolvedReferences
    return internet.TCPClient(hostname, port, BattlesnakeTelnetFactory())