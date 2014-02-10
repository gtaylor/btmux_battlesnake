import os
import inspect

from zope.interface import implements
from twisted.application import service
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from battlesnake.conf import read_config
from battlesnake.core.services.telnet import get_telnet_service


class Options(usage.Options):
    optParameters = [
        ["config", "c", "battlesnake.cfg", "The configuration file to use."]
    ]


# noinspection PyPep8Naming
class ServiceMaker(object):
    """
    This class creates a MultiService and returns it for the twistd command's
    plugin system to run.
    """

    implements(IServiceMaker, IPlugin)
    tapname = "battlesnake"
    description = "Runs a Battlesnake client."
    options = Options

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))))

    def makeService(self, options):
        """
        And away we go!

        :param Options options:
        """

        read_config(options['config'])
        top_service = service.MultiService()

        telnet_service = get_telnet_service()
        telnet_service.setServiceParent(top_service)

        return top_service


# This is where the Twisted magic takes over.
serviceMaker = ServiceMaker()
