"""
This module contains everything needed to manipulate a unit's ``mechdamage``
XCODE attribute.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.core.utils import add_escaping_percent_sequences
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands.mux_commands import remit, trigger
from battlesnake.outbound_commands.think_fn_wrappers import btgetxcodevalue, \
    btsetxcodevalue, get_map_dimensions, get

from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    choose_unit_spawn_spot
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import DEFENDER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


FIXER_REFS = ['ArmorFixer', 'InternalsFixer', 'AmmoReloader']


@inlineCallbacks
def uniformly_repair_armor(protocol, unit_dbref, percent_fix):
    """
    Given a unit and a percentage, uniformly reduce the armor damage in each
    section by the given percentage.

    :param str unit_dbref: Dbref of the unit to fix.
    :param float percent_fix: The percentage of damage to repair in each
        section on the unit. Range of 0...1.
    """

    # Looks something like: A:0/5,A(R):3/5,A(R):4/5
    damages = yield btgetxcodevalue(protocol, unit_dbref, 'mechdamage')
    section_split = damages.split(',')
    # This will store the new modified values for section damages.
    modified_sections = []
    for section in section_split:
        if not section:
            continue
        if not section.startswith('A'):
            # Not armor, no fix for you.
            modified_sections.append(section)

        sec_id, damage_level = section.split('/')
        damage_level = int(damage_level)
        repair_amount = int(damage_level * float(percent_fix))
        new_damage_level = damage_level - repair_amount
        if new_damage_level <= 0:
            # Don't re-add this section to damages, it's been fully repaired.
            continue
        # Re-combine the new damage level with the section ID.
        new_section_value = sec_id + '/%d' % new_damage_level
        # Push this back into a list of modified sections to be set on the unit.
        modified_sections.append(new_section_value)

    modified_damages = _assemble_modified_damages(modified_sections)
    yield btsetxcodevalue(protocol, unit_dbref, 'mechdamage', modified_damages)
    message = (
        "%ch%cg%%{int_perc}%cw of your unit's armor damage has been repaired."
        "%cn".format(int_perc=int(percent_fix * 100)))
    remit(protocol, unit_dbref, message)


@inlineCallbacks
def fix_all_internals(protocol, unit_dbref):
    """
    Repairs all of a unit's internals.

    :param str unit_dbref: Dbref of the unit to fix.
    """

    # Looks something like: A:0/5,A(R):3/5,A(R):4/5
    damages = yield btgetxcodevalue(protocol, unit_dbref, 'mechdamage')
    section_split = damages.split(',')
    # This will store the new modified values for section damages.
    modified_sections = []
    for section in section_split:
        if not section:
            continue
        if not section.startswith('I'):
            # Not internals, no fix for you.
            modified_sections.append(section)
        # All of the internals get left out of the modified list, thus fixing
        # them all.

    modified_damages = _assemble_modified_damages(modified_sections)
    yield btsetxcodevalue(protocol, unit_dbref, 'mechdamage', modified_damages)
    message = "%chYour unit's internal damage has been completely repaired.%cn"
    remit(protocol, unit_dbref, message)


@inlineCallbacks
def reload_all_ammo(protocol, unit_dbref):
    """
    Reloads all depleted ammo on a unit.

    :param str unit_dbref: Dbref of the unit to fix.
    """

    # Looks something like: A:0/5,A(R):3/5,A(R):4/5
    damages = yield btgetxcodevalue(protocol, unit_dbref, 'mechdamage')
    section_split = damages.split(',')
    # This will store the new modified values for section damages.
    modified_sections = []
    for section in section_split:
        if not section:
            continue
        if not section.startswith('R'):
            # Not missing ammo, no fix for you.
            modified_sections.append(section)
        # All of the internals get left out of the modified list, thus fixing
        # them all.

    modified_damages = _assemble_modified_damages(modified_sections)
    yield btsetxcodevalue(protocol, unit_dbref, 'mechdamage', modified_damages)
    message = "%chYour unit's ammo stores have been completely reloaded.%cn"
    remit(protocol, unit_dbref, message)


def _assemble_modified_damages(modified_sections):
    """
    :param list modified_sections: A list of modified section damage values,
        in their original order.
    :rtype: str
    :return: A correctly re-joined, escaped damages string that is ready to
        be set on the unit via btsetxcodevalue().
    """

    modified_damages = ','.join(modified_sections)
    # We have to escape the parenthesis and the commas to get this through
    # btsetxcodevalue() correctly.
    escaped_damages = add_escaping_percent_sequences(modified_damages)
    escaped_damages = escaped_damages.replace(',', '%,')
    return escaped_damages


@inlineCallbacks
def spawn_fixer_unit(protocol, map_dbref, fixer_type, fix_percent):
    """
    Spawning logic for fixer units.

    :param str map_dbref: The dbref of the map to spawn the fixer on.
    :param str fixer_type: One of the refs in :py:var:`FIXER_REFS`.
    :param float fix_percent: For armor fixer, percentage of armor to fix.
        Ignored for other types. Range is 0...1.
    :return:
    """

    p = protocol
    if fixer_type == 'armor':
        unit_ref = 'ArmorFixer'
        fix_percent = fix_percent
    elif fixer_type == 'ints':
        unit_ref = 'InternalsFixer'
        fix_percent = 1.0
    elif fixer_type == 'ammo':
        unit_ref = 'AmmoReloader'
        fix_percent = 1.0
    else:
        raise ValueError('Invalid fixer type: %s' % fixer_type)

    faction = get_faction(DEFENDER_FACTION_DBREF)
    map_width, map_height = yield get_map_dimensions(p, map_dbref)
    # This currently spawns in the same patterns as the attacker AI.
    unit_x, unit_y = choose_unit_spawn_spot(map_width, map_height)
    extra_status_flags = ['COMBAT_SAFE', 'AUTOCON_WHEN_SHUTDOWN']
    extra_attrs = {'FIXER_FIX_PERCENT': fix_percent}
    yield create_unit(protocol, unit_ref, map_dbref, faction,
        unit_x, unit_y, extra_status_flags=extra_status_flags,
        extra_attrs=extra_attrs)


def check_unit_for_fixer_use(puppet, unit):
    """
    Given a unit, see if they ran into any unused fixers on the map.

    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit unit: The newly updated unit.
    """

    hex_neighbors = puppet.unit_store.find_units_in_hex(
        unit.x_coord, unit.y_coord)
    for neighbor in hex_neighbors:
        if neighbor.unit_ref in FIXER_REFS and not neighbor.has_been_ran_over:
            print "%s used fixer %s" % (unit, neighbor)
            use_fixer_unit(puppet, unit, neighbor)


@inlineCallbacks
def use_fixer_unit(puppet, unit, fixer_unit):
    """
    Given a unit and a fixer unit, consume the fixer to fix the user.

    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit unit: The unit being fixed.
    :param ArenaMapUnit fixer_unit: The fixer unit to use.
    """

    p = puppet.protocol
    # Prevent this fixer from being used multiple times.
    fixer_unit.has_been_ran_over = True
    # Start destroying it immediately.
    trigger(p, fixer_unit.dbref, 'DESTMECH.T')
    fix_percent = yield get(p, fixer_unit.dbref, 'FIXER_FIX_PERCENT')
    fix_percent = float(fix_percent)

    emit_cmd = "@losemit uses %[{fixer_id}%] {fixer_mechname}.".format(
        fixer_id=fixer_unit.contact_id, fixer_mechname=fixer_unit.mech_name)
    mux_commands.force(p, unit.dbref, emit_cmd)

    if fixer_unit.unit_ref == 'ArmorFixer':
        yield uniformly_repair_armor(p, unit.dbref, fix_percent)
    elif fixer_unit.unit_ref == 'InternalsFixer':
        yield fix_all_internals(p, unit.dbref)
    elif fixer_unit.unit_ref == 'AmmoReloader':
        yield reload_all_ammo(p, unit.dbref)
