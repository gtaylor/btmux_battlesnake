"""
Contains some useful unit manipulation sequences.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands.think_fn_wrappers import btgetxcodevalue, \
    btsetxcodevalue

# Maps friendly string names to the various status/critstatus flags. The
# tuple is in the form of (xcode_attr, flag_char).
FLAG_MAP = {
    'PERFORMING_ACTION': ('status', 'j'),
    'COMBAT_SAFE': ('status', 'w'),
    'AUTOCON_WHEN_SHUTDOWN': ('status', 'x'),

    'AUTOTURN_TURRET': ('status2', 'o'),
    'ATTACKEMIT_MECH': ('status2', 't'),
    'FORTIFIED': ('status2', 'w'),
    'WEAPONS_HOLD': ('status2', 'x'),
    'NO_GUN_XP': ('status2', 'y'),

    'CLAIRVOYANT': ('critstatus', 'y'),
    'INVISIBLE': ('critstatus', 'A'),
    'OBSERVATORIC': ('critstatus', 'C'),
}


@inlineCallbacks
def add_unit_status_flags(protocol, unit_dbref, status_flags):
    """
    Given a unit, add the specified status flags if they are not already present.

    :param str unit_dbref: A valid MECH xcode object's dbref.
    :param list status_flags: A list of any of the flags in ``FLAG_MAP``.
    """

    p = protocol
    flags_to_set = {}
    for flag in status_flags:
        if flag not in FLAG_MAP:
            raise ValueError("Invalid status flag: %s" % flag)

        xcode_attr = FLAG_MAP[flag][0]
        xcode_val = FLAG_MAP[flag][1]
        if xcode_attr not in flags_to_set:
            flags_to_set[xcode_attr] = xcode_val
        else:
            flags_to_set[xcode_attr] += xcode_val

    for xcode_attr, new_flags in flags_to_set.items():
        current_vals = yield btgetxcodevalue(p, unit_dbref, xcode_attr)
        current_set = set(list(current_vals))
        new_set = set(list(new_flags))
        combined_set = current_set.union(new_set)
        new_val = ''.join(combined_set)
        yield btsetxcodevalue(p, unit_dbref, xcode_attr, new_val)