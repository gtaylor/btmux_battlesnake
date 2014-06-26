"""
This module contains everything needed to manipulate a unit's ``mechdamage``
XCODE attribute.
"""

from twisted.internet.defer import inlineCallbacks
from battlesnake.core.utils import add_escaping_percent_sequences

from battlesnake.outbound_commands.mux_commands import remit
from battlesnake.outbound_commands.think_fn_wrappers import btgetxcodevalue, \
    btsetxcodevalue


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
