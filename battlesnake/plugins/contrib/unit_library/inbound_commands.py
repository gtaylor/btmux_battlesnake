from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.unit_library.outbound_commands import \
    load_ref_in_templater
from battlesnake.plugins.contrib.unit_library.unit_scanning.api import \
    scan_unit_from_templater


class ScanUnitCommand(BaseCommand):
    """
    Scans a unit into the unit library.
    """

    command_name = "ul_scanunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        reference = parsed_line.kwargs['reference']
        pval = "Re-loading %s in templater..." % reference
        yield mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)
        yield load_ref_in_templater(protocol, reference)
        yield scan_unit_from_templater(protocol, invoker_dbref)


class LoadUnitCommand(BaseCommand):
    """
    Loads a unit into the templater.
    """

    command_name = "ul_loadunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        reference = parsed_line.kwargs['reference']
        pval = "Loading %s in templater..." % reference
        yield mux_commands.pemit(protocol, parsed_line.invoker_dbref, pval)
        yield load_ref_in_templater(protocol, reference)


class UnitLibraryCommandTable(InboundCommandTable):

    commands = [
        ScanUnitCommand,
        LoadUnitCommand,
    ]
