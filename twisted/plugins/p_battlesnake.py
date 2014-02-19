from zope.interface import implements
from twisted.application import service
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from battlesnake.core.py_importer import import_class


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

    def makeService(self, options):
        """
        And away we go! We import the battlesnake stuff in here to ensure
        the correct import order. Need to make sure the settings have been
        imported and populated first.

        :param Options options:
        """

        from battlesnake.conf import read_config
        read_config(options['config'])
        top_service = service.MultiService()

        from battlesnake.core.services.telnet import get_telnet_service
        telnet_service = get_telnet_service()
        telnet_service.setServiceParent(top_service)

        self.load_extra_services(top_service)

        return top_service

    def load_extra_services(self, top_service):
        """
        If the user has added additional services in their config file,
        load and start them.
        """

        from battlesnake.conf import settings
        extra_services = settings['bot']['extra_services']
        if not extra_services:
            print "NO SERVICES"
            return
        print "Loading extra services..."
        for svc_loader in extra_services:
            print "  - Loading %s" % svc_loader
            loader = import_class(svc_loader)
            svc = loader()
            svc.setServiceParent(top_service)


# This is where the Twisted magic takes over.
serviceMaker = ServiceMaker()
