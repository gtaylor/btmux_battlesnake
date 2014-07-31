import random
from collections import deque


def divide_salvage(salvage_dict, num_divisions, skip_chance):
    """
    Given a dict of salvage to split, divide it up ``num_divisions`` way.
    This is done by taking turns, with a chance to lose your turn entirely
    with a bad roll (thus taking a certain quantity of salvage out of play).

    :param dict salvage_dict: The salvage to split. Keys are item names,
        values are quantity.
    :param int num_divisions: The number of ways to split the salvage.
    :param int skip_chance: A number 0-100 that determines the percent
        chance that a salvage turn will be skipped. 90 = 90% chance, etc.
    :rtype: list
    :returns: A list of salvage dicts, divided up semi-randomly.
    """

    # This will hold our divided salvage dict.
    divided = {k: {} for k in range(0, num_divisions)}
    # Keeps track of whose turn it is to draw salvage.
    turn_tracker = deque(range(0, num_divisions))

    for iname, iremaining in salvage_dict.items():
        if iname.startswith('Ammo_'):
            continue
        while iremaining > 0:
            who = turn_tracker.popleft()
            turn_tracker.append(who)
            num_awarded = random.randint(0, iremaining)
            if num_awarded == 0:
                # Bummer, dude.
                continue
            if random.randint(0, 100) <= skip_chance:
                # Randomly discarded. Ouch.
                iremaining -= num_awarded
                continue
            if iname not in divided[who]:
                divided[who][iname] = num_awarded
            else:
                divided[who][iname] += num_awarded
            iremaining -= num_awarded

    return divided
