from twisted.application import internet

from battlesnake.conf import settings
from battlesnake.plugins.imc2.imc2 import IMC2BotFactory


def get_imc2_service(telnet_service):
    """
    Instantiates an appropriate service instance for the telnet client.

    :returns: The TCPClient based Telnet service.
    """

    _, _, telnet_factory = telnet_service.args
    hostname = settings['imc2']['hub_hostname']
    port = settings['imc2']['hub_port']
    factory = IMC2BotFactory(telnet_factory=telnet_factory)
    # noinspection PyUnresolvedReferences
    return internet.TCPClient(hostname, port, factory)
