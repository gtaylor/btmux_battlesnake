import os

from twisted.internet.defer import inlineCallbacks
from btmux_template_io.parser import parse_from_file

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.base import CommandError
from battlesnake.outbound_commands.think_fn_wrappers import btgetbv2_ref, \
    btgetxcodevalue, btfasabasecost_ref, btgetbv_ref, bttechlist_ref

from battlesnake.plugins.contrib.unit_library.api import save_unit_to_db


@inlineCallbacks
def scan_unit_from_templater(protocol, invoker_dbref):
    """
    Scans the current unit loaded in the templater into the DB.

    :param str invoker_dbref: The invoker's dbref string.
    """

    p = protocol
    templater_dbref = settings['unit_library']['templater_dbref']

    unit_ref = yield btgetxcodevalue(p, templater_dbref, 'mechref')
    # Now that we have the reference name with correct capitalization, switch
    # over to btgetxcodevalue_ref() calls to pull from saved values.

    # The template files sometimes have this in them, but we can calculate
    # it dynamically in-game.
    bv = yield btgetbv_ref(p, unit_ref)
    bv2 = yield btgetbv2_ref(p, unit_ref)
    base_cost = yield btfasabasecost_ref(p, unit_ref)
    tech_list = yield bttechlist_ref(p, unit_ref)
    unit = _load_template_from_mechs_dir(unit_ref)

    # Marshall the unit and send it to the DB.
    yield save_unit_to_db(unit, bv, bv2, base_cost, tech_list)


def _load_template_from_mechs_dir(unit_ref):
    """
    Given a unit reference, load the template file by the same name from the
    game's ``mechs`` directory.

    :param str unit_ref: The unit reference to scan.
    :rtype: btmux_template_io.unit.BTMuxUnit
    """

    mechs_dir = settings['unit_library']['mechs_dir_path']
    if not mechs_dir:
        raise CommandError("unit_library -> mechs_dir_path setting has no value.")
    mech_path = os.path.join(mechs_dir, unit_ref)
    if not os.path.exists(mech_path):
        raise CommandError("You'll need to SAVENEW the unit before scanning.")
    unit = parse_from_file(mech_path)
    return unit
