from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands


class ScanUnitCommand(BaseCommand):
    """
    Scans a unit into the unit library.
    """

    command_name = "ul_scanunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        template_pod_dbref = parsed_line.kwargs['template_pod_dbref']
        reference = parsed_line.kwargs['reference']
        pval = "Scanning %s..." % reference
        yield mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)


class UnitLibraryCommandTable(InboundCommandTable):

    commands = [
        ScanUnitCommand,
    ]
