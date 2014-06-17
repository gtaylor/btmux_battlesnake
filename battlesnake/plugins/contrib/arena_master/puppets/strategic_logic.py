import random
from battlesnake.plugins.contrib.arena_master.puppets import outbound_commands as ai_commands


# This is the maximum number of tics that a unit can be speed 0.0 with
# a destination before we try to assign a new one.
MAX_IDLE_COUNTER = 25


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

        if unit.is_fallen():
            unit.ai_idle_counter = 0
            continue

        if unit.speed != 0.0 and not unit.is_at_ai_destination():
            # He's moving, don't bother him.
            unit.ai_idle_counter = 0
            continue

        if unit.target_dbref != '#-1':
            unit.ai_idle_counter = 0
            continue

        if unit.speed == 0.0 and unit.ai_last_destination and \
           unit.ai_idle_counter < MAX_IDLE_COUNTER:
            # This unit has a destination but is sitting still. Increment
            # the idle timer, don't try to order it to do anything.
            # Once the counter gets high enough, we'll fall through to
            # the order section.
            print "+Idle", \
                unit, unit.ai_last_destination, unit.ai_idle_counter
            unit.ai_idle_counter += 1
            continue

        if unit.ai_last_destination and not unit.is_at_ai_destination() and \
           unit.ai_idle_counter < MAX_IDLE_COUNTER:
            # He's got something to do, don't bother him.
            continue

        # We're going to tell them to do something. Reset the idle counter.
        unit.ai_idle_counter = 0

        print "Unit needs new orders:", unit
        print "  - Last destination", unit.ai_last_destination
        new_dest = get_logical_roam_destination(puppet)
        print "  - New destination", new_dest

        unit.ai_last_destination = new_dest
        move_orders = "{ai_id} goto {x} {y}".format(
            ai_id=unit.contact_id, x=new_dest[0], y=new_dest[1])
        ai_commands.order_ai(protocol, puppet, move_orders)
        chase_orders = "{ai_id} chasetarg on".format(ai_id=unit.contact_id)
        ai_commands.order_ai(protocol, puppet, chase_orders)


def handle_ai_target_change(puppet, old_unit, new_unit):
    """
    This gets called when an AI's target changes.

    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit old_unit: The old version of the unit in the
        store. This doesn't have the new changes that were picked up.
    :param ArenaMapUnit new_unit: The new unit instance generated from
        polling the units on the map. The store will copy over the
        changed attributes from this instance to ``old_unit`` after this
        handler runs.
    """

    protocol = puppet.protocol
    aggressor_id = old_unit.contact_id
    if new_unit.target_dbref == '#-1':
        # Had a lock but lost it.
        return
    # If we get this far, the AI has a new lock. They need to follow
    # this guy.
    victim = puppet.unit_store.get_unit_by_dbref(new_unit.target_dbref)
    victim_id = victim.contact_id

    # We clear these out so that a new destination may be assigned immediately
    # if something happens to the target and the unit comes to a stop.
    old_unit.ai_last_destination = None
    new_unit.ai_last_destination = None

    chase_orders = "{aggressor_id} follow {victim_id}".format(
        aggressor_id=aggressor_id, victim_id=victim_id)
    ai_commands.order_ai(protocol, puppet, chase_orders)
