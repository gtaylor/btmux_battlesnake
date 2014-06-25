import os

from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.core.ansi import ANSI_NORMAL, \
    ANSI_HI_GREEN, ANSI_HI_YELLOW, ANSI_HI_RED, ANSI_HI_MAGENTA
from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.unit_library.api import get_unit_by_ref, \
    get_library_summary_list
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
        # TODO: Import these but make them hidden in the DB.
        skipped_refs = [
            'MechWarrior', 'RadioTower',
        ]

        for template_file in os.listdir(mechs_dir_path):
            full_path = os.path.join(mechs_dir_path, template_file)
            if template_file in skipped_refs or template_file.startswith('.'):
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


class ListrefsCommand(BaseCommand):
    """
    Lists unit refs.
    """

    command_name = "ul_listrefs"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        class_choices = ['light', 'medium', 'heavy', 'assault']
        type_choices = ['mech', 'tank', 'vtol', 'battlesuit']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="listrefs", description='Lists unit references.')

        parser.add_argument(
            "--class", type=str, choices=class_choices, dest='filter_class',
            help="Mech weight class to filter by")

        parser.add_argument(
            "--type", type=str, choices=type_choices, dest='filter_type',
            help="Unit type to filter by")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        lib_summary = yield get_library_summary_list(
            filter_class=args.filter_class, filter_type=args.filter_type)
        pval = self._get_header_str('Unit Reference Listing : %d results' % len(lib_summary['refs']))
        pval += '%r%b%b'
        for counter, udict in enumerate(lib_summary['refs'], start=1):
            weight = udict['weight']
            if weight < 40:
                class_color = ANSI_HI_GREEN
            elif weight < 60:
                class_color = ANSI_HI_YELLOW
            elif weight < 80:
                class_color = ANSI_HI_RED
            else:
                class_color = ANSI_HI_MAGENTA
            pval += "[ljust({class_color}{reference}{ansi_normal}, 18)]".format(
                class_color=class_color,
                reference=udict['reference'],
                ansi_normal=ANSI_NORMAL,
            )
            if counter % 4 == 0:
                pval += "%r%b%b"
        pval += self._get_footer_str(pad_char='-')
        pval += '%r[space(5)]'
        pval += '[ljust(%ch%cgLight,20)]'
        pval += '[ljust(%ch%cyMedium, 20)]'
        pval += '[ljust(%ch%crHeavy, 20)]'
        pval += '%ch%cmAssault'
        pval += '%r[space(22)]%cnFor more info, type %ch%cglistrefs -h'
        pval += self._get_footer_str()
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class UnitLibraryCommandTable(InboundCommandTable):

    commands = [
        ScanUnitCommand,
        ScanLibraryCommand,
        LoadUnitCommand,
        ListrefsCommand,
    ]
