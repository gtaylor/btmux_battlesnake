import math
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

    for name, num_weaps in weapons_payload:
        weapon_dat = WEAPON_TABLE[name]
        if not weapon_dat.get('is_offensive', True):
            # Probably AMS or someshit.
            continue
        # If the weapon appears multiple times, the range gets added to
        # the range list multiple times.
        range_list += [weapon_dat['medium_range']] * num_weaps

    if range_list:
        range_avg = math.floor(numpy.average(range_list))
        return max(2, int(range_avg))
    else:
        # Has no weapons. Assume (probably wrongly) physical/melee only.
        return 0
