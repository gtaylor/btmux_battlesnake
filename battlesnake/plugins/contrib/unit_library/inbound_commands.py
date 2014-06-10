import os

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
        yield self._scan_unit(protocol, invoker_dbref, reference)

    @inlineCallbacks
    def _scan_unit(self, protocol, invoker_dbref, reference):
        templater_dbref = settings['unit_library']['templater_dbref']
        pval = "Re-loading %s in templater..." % reference
        yield mux_commands.remit(protocol, templater_dbref, pval)
        yield load_ref_in_templater(protocol, reference)
        yield scan_unit_from_templater(protocol, invoker_dbref)
        yield mux_commands.remit(
            protocol, templater_dbref,
            "Finished scanning %s" % reference)


class ScanLibraryCommand(ScanUnitCommand):
    """
    Scans all template files in the mechs directory into the template library.
    """

    command_name = "ul_scanlibrary"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        mechs_dir_path = settings['unit_library']['mechs_dir_path']
        templater_dbref = settings['unit_library']['templater_dbref']

        for template_file in os.listdir(mechs_dir_path):
            full_path = os.path.join(mechs_dir_path, template_file)
            if template_file == 'Mechwarrior' or template_file.startswith('.'):
                continue
            if not os.path.isfile(full_path):
                continue
            yield mux_commands.remit(
                protocol, templater_dbref,
                "Attempting to scan %s" % template_file)
            yield self._scan_unit(protocol, invoker_dbref, template_file)


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
        ScanLibraryCommand,
        LoadUnitCommand,
    ]
