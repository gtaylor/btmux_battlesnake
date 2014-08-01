import os
import itertools
from pprint import pformat

from twisted.internet.defer import inlineCallbacks
from btmux_template_io.item_table import WEAPON_TABLE
from btmux_template_io.special_techs import TECH_TABLE

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
from battlesnake.outbound_commands import think_fn_wrappers

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

        for template_file in os.listdir(mechs_dir_path):
            full_path = os.path.join(mechs_dir_path, template_file)
            if template_file.startswith('.'):
                continue
            if not os.path.isfile(full_path):
                continue
            yield mux_commands.remit(
                protocol, templater_dbref,
                "Attempting to scan %s" % template_file)
            yield self._scan_unit(protocol, invoker_dbref, template_file)


class PrintWeaponTableCommand(ScanUnitCommand):
    """
    Pulls the weapon table from btmux_template_io, populates it with
    the latest range/vrt values and spits it out to to a text file..
    """

    command_name = "ul_printweaponstable"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        mux_commands.pemit(p, invoker_dbref, "Beginning weapons table dump.")
        for weap_name, val in WEAPON_TABLE.items():
            new_val = yield think_fn_wrappers.btweapstat(protocol, weap_name)
            val.update(new_val)
            WEAPON_TABLE[weap_name] = val
        fobj = open('weapons_table.txt', 'w')
        fobj.write(pformat(WEAPON_TABLE))
        fobj.close()
        mux_commands.pemit(p, invoker_dbref, "Table dumped to weapons_table.txt.")


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
        try:
            yield get_unit_by_ref(reference)
        except ValueError:
            yield mux_commands.remit(
                protocol, templater_dbref,
                "WARNING: %s is not in the unit library." % reference)
        yield mux_commands.remit(
            protocol, templater_dbref,
            "Finished loading %s" % reference)


class UnitSpecsCommand(BaseCommand):
    """
    Powers viewref/specs.
    """

    command_name = "ul_unitspecs"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        unit_ref = parsed_line.kwargs['unit_ref']
        try:
            unit = yield get_unit_by_ref(unit_ref)
        except ValueError:
            raise CommandError("Invalid reference.")

        header_txt = "%cy{unit_ref} %cr{unit_name}%cn".format(
            unit_ref=unit.reference, unit_name=unit.name,
        )
        retval = self._get_header_str(header_txt)
        retval += (
            " [rjust(Type,{col1rjust})]: [ljust({unit_type},{col1ljust})]"
            " [rjust(Tonnage,{col2rjust})]: [ljust({weight},{col2ljust})]"
            " Class: {weight_class}%r"
            ""
            " [rjust(Speed,{col1rjust})]: [ljust({walk_mp}/{run_mp}/{jj_total},{col1ljust})]"
            " [rjust(Armor/Int,{col2rjust})]: [ljust({armor_total}/{internals_total},{col2ljust})]"
            " HSinks: {heatsink_total}%r"
            ""
            " [rjust(BV2,{col1rjust})]: [ljust(round(BTGETBV2_REF({unit_ref}),0),{col1ljust})]"
            " [rjust(Off-BV2,{col2rjust})]: [ljust(round(BTGETOBV_REF({unit_ref}),0),{col2ljust})]"
            " Def-BV2: [round(BTGETDBV_REF({unit_ref}),0)]%r"
            ""
            " [rjust(Mfg,{col1rjust})]: {manufacturer}".format(
                unit_type=unit.unit_type, weight=unit.weight,
                weight_class=unit.weight_class, walk_mp=unit.walk_mp,
                run_mp=unit.run_mp, jj_total=unit.jumpjet_total,
                armor_total=unit.armor_total, internals_total=unit.internals_total,
                heatsink_total=unit.heatsink_total,
                unit_ref=unit.reference,
                manufacturer=unit.manufacturer if unit.manufacturer else 'Unknown',
                col1rjust=9, col1ljust=19,
                col2rjust=9, col2ljust=19
            ))
        retval += self._get_subheader_str('Weapons and Ammo')
        retval += self._section_ammo_and_weaps(unit)
        retval += self._get_subheader_str('Special Technology')
        retval += self._section_specials(unit)
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)

    def _section_ammo_and_weaps(self, unit):
        weapons_payload = unit.weapons_payload
        ammo_payload = unit.ammo_payload
        payload_iter = itertools.izip_longest(
            weapons_payload.items(), ammo_payload.items())
        retval = ""
        for weapon, ammo in payload_iter:
            if weapon:
                weap_name, weap_count = weapon
                weap_string = "{weap_count}x {weap_name}".format(
                    weap_count=weap_count, weap_name=weap_name)
            else:
                weap_string = ''

            if ammo:
                ammo_name, ammo_data = ammo
                ammo_string = "{ammo_tons} tons of {ammo_name} %({shots:,} shots%)".format(
                    ammo_tons=ammo_data['tons'], ammo_name=ammo_name,
                    shots=ammo_data['shots'])
            else:
                ammo_string = ''

            retval += "%r [ljust({weap_string},30)]{ammo_string}".format(
                weap_string=weap_string, ammo_string=ammo_string)
        return retval

    def _section_specials(self, unit):
        retval = ""
        for short_name in unit.specials:
            retval += "%r " + TECH_TABLE[short_name]['name']
        return retval


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
        PrintWeaponTableCommand,

        ListrefsCommand,
        UnitSpecsCommand,
    ]
