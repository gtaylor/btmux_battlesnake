from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.base import BaseCommand
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.unit_library.api import get_unit_by_ref
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
        templater_dbref = settings['unit_library']['templater_dbref']
        pval = "Re-loading %s in templater..." % reference
        yield mux_commands.remit(protocol, templater_dbref, pval)
        yield load_ref_in_templater(protocol, reference)
        yield scan_unit_from_templater(protocol, invoker_dbref)
        yield mux_commands.remit(
            protocol, templater_dbref,
            "Finished scanning %s" % reference)


class LoadUnitCommand(BaseCommand):
    """
    Loads a unit into the templater.
    """

    command_name = "ul_loadunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        reference = parsed_line.kwargs['reference']
        templater_dbref = settings['unit_library']['templater_dbref']
        yield mux_commands.remit(
            protocol, templater_dbref,
            "Loading %s in templater..." % reference)
        yield load_ref_in_templater(protocol, reference)
        unit = yield get_unit_by_ref(reference)
        if not unit:
            yield mux_commands.remit(
                protocol, templater_dbref,
                "WARNING: %s is not in the unit library." % reference)
        yield mux_commands.remit(
            protocol, templater_dbref,
            "Finished loading %s" % reference)


class UnitLibraryCommandTable(InboundCommandTable):

    commands = [
        ScanUnitCommand,
        LoadUnitCommand,
    ]
