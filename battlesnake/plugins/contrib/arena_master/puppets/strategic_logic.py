import random
from battlesnake.plugins.contrib.arena_master.puppets import outbound_commands as ai_commands


def get_logical_roam_destination(puppet, edge_padding=8):
    """
    Since we're relying on smaller maps to make sure that our AI eventually
    stumbles across an enemy, pick a random hex that isn't near (but not on)
    the map boundary.

    :param ArenaMasterPuppet puppet:
    :param int edge_padding: This is the closest a unit can get to the
        map borders. This increases the chance of running into enemy units
        and keeps the AI away from the map edges, where they tend to suck.
    :rtype: tuple
    :returns: A destination tuple in the form of (x,y).
    """

    map_width = puppet.map_width - 1
    map_height = puppet.map_height - 1

    min_x = edge_padding
    max_x = map_width - edge_padding
    min_y = edge_padding
    max_y = map_height - edge_padding

    x = min(max(random.randint(0, map_width), min_x), max_x)
    y = min(max(random.randint(0, map_height), min_y), max_y)
    return x, y


def move_idle_units(puppet, friendly_ai_units):
    """
    Given a list of ArenaMapUnit instances, put any idle slackers to work.

    :param ArenaMasterPuppet puppet:
    :param list units:
    """

    protocol = puppet.protocol

    for unit in friendly_ai_units:
        if unit.is_immobile():
            # Lost cause.
            continue

        if unit.speed != 0.0 and not unit.is_at_ai_destination():
            # He's moving, don't bother him.
            continue

        if unit.ai_last_destination and not unit.is_at_ai_destination():
            # He's got something to do, don't bother him.
            continue

        print "Unit needs new orders:", unit
        print "  - Last destination", unit.ai_last_destination
        new_dest = get_logical_roam_destination(puppet)
        print "  - New destination", new_dest

        unit.ai_last_destination = new_dest
        move_orders = "{ai_id} dgoto {x} {y}".format(
            ai_id=unit.contact_id, x=new_dest[0], y=new_dest[1])
        ai_commands.order_ai(protocol, puppet, move_orders)
        chase_orders = "{ai_id} chasetarg on".format(ai_id=unit.contact_id)
        ai_commands.order_ai(protocol, puppet, chase_orders)
