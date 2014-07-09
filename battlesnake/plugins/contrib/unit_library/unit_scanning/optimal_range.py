import numpy

from btmux_template_io.item_table import WEAPON_TABLE


def get_estimated_optimal_weapons_range(unit):
    """
    Returns an estimated optimal weapons range. This doesn't consider
    armor or mobility, and isn't going to work well for all ranged units.
    We calculate all of this pretty naively, too. There's probably a
    better way.

    :rtype: int
    :returns: The optimal weapons range for this mech.
    """

    range_list = []
    weapons_payload = unit.weapons_payload.items()

    for name, dat in weapons_payload:
        weapon_dat = WEAPON_TABLE[name]
        if not weapon_dat.get('is_offensive', True):
            # Probably AMS or someshit.
            continue
        range_list.append(weapon_dat['medium_range'])

    if range_list:
        return max(2, int(numpy.average(range_list)))
    else:
        return 0
