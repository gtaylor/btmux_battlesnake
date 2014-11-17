from twisted.application import internet

from battlesnake.conf import settings
from battlesnake.plugins.imc2.imc2 import IMC2BotFactory


def get_imc2_service():
    """
    Instantiates an appropriate service instance for the telnet client.

    :returns: The TCPClient based Telnet service.
    """

    hostname = settings['imc2']['hub_hostname']
    port = settings['imc2']['hub_port']
    factory = IMC2BotFactory()
    # noinspection PyUnresolvedReferences
    return internet.TCPClient(hostname, port, IMC2BotFactory())
