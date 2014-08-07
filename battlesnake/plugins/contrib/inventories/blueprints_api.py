import random
from collections import OrderedDict

from psycopg2 import IntegrityError
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.inventories.defines import BLUEPRINT_TYPES, \
    BP_TYPE_COLORS
from battlesnake.plugins.contrib.inventories.exceptions import \
    InsufficientInventory


@inlineCallbacks
def draw_random_blueprint(draw_chance):
    """
    Carries out a roll for a chance to draw a random blueprint.

    :param int draw_chance: A number 0-100, representing the percent chance
        to draw a BP.
    :rtype: tuple
    :returns: A tuple in the form of (bp_ref, bp_type).
    """

    cutoff = 100 - int(draw_chance)
    roll = random.randint(0, 100)

    if roll < cutoff:
        returnValue((None, None))

    query = (
        "SELECT reference FROM unit_library_unit "
        "  WHERE is_player_spawnable=True ORDER BY random() LIMIT 1"
    )

    # Clone the list so we don't mess with the define.
    bp_types = BLUEPRINT_TYPES[:]
    random.shuffle(bp_types)

    conn = yield get_db_connection()
    results = yield conn.runQuery(query)
    for result in results:
        returnValue((result[0], bp_types[0]))


@inlineCallbacks
def reward_random_blueprint(protocol, player_dbref, draw_chance):
    bp_ref, bp_type = yield draw_random_blueprint(draw_chance)
    if not bp_ref:
        returnValue((None, None))
    bp_mods = [
        {'unit_ref': bp_ref, 'bp_type': bp_type, 'mod_amount': 1},
    ]
    yield modify_player_blueprint_inventory(player_dbref, bp_mods)
    message = (
        "%chYou have been rewarded a %cy{bp_ref}%cw "
        "%({bp_type_color}{bp_type}%ch%cw%) "
        "blueprint for your performance! Type %cgblueprints%cw to see "
        "your full inventory of blueprints%cn".format(
            bp_type=bp_type, bp_ref=bp_ref,
            bp_type_color=BP_TYPE_COLORS[bp_type]))
    mux_commands.pemit(protocol, player_dbref, message)
    returnValue((bp_ref, bp_type))


@inlineCallbacks
def check_player_blueprint_levels(player_dbref, bp_mods):
    """
    Given a list of required blueprint dicts, look through
    the player's inventory and see what (if any) items are missing.

    If certain blueprints are found to be at inadequate levels, said bp(s)
    will end up in the returned dict with the value being how many additional
    blueprints are needed.

    :param str player_dbref: The dbref of the player whose inventory to check.
    :param list bp_mods: A list of dicts containing the blueprint inventory
        level modifications. Positive = add, negative = subtract BPs.
        Each dict dict is in the form of
        ``{'unit_ref': ..., 'bp_type": ..., 'mod_amount': ...}```.
    :rtype: dict
    :return: A list of blueprint dicts that the player needs more of.
        If they have everything, this is an empty list.
    """

    owner_id = int(player_dbref[1:])
    unit_ids = [bp_dict['unit_ref'] for bp_dict in bp_mods]
    query = (
        "SELECT unit_id, bp_type, quantity FROM inventories_ownedunitblueprint "
        "  WHERE quantity > 0 AND owner_id=%s AND unit_id = ANY(%s) "
    )

    conn = yield get_db_connection()
    results = yield conn.runQuery(query, (owner_id, unit_ids))

    available_dict = {}
    for result in results:
        unit_id = result['unit_id']
        bp_type = result['bp_type']
        key = '%s!%s' % (unit_id, bp_type)
        if key not in available_dict:
            available_dict[key] = result['quantity']
        else:
            available_dict[key] += result['quantity']

    required_dict = {}
    for req in bp_mods:
        key = '%s!%s' % (req['unit_ref'], req['bp_type'])
        if key not in required_dict:
            required_dict[key] = req['mod_amount']
        else:
            required_dict[key] += req['mod_amount']

    missing = []
    for key, required_count in required_dict.items():
        if required_count >= 0:
            continue
        available_count = available_dict.get(key, 0)
        if available_count < abs(required_count):
            unit_id, bp_type = key.split('!')
            missing.append({
                'unit_ref': unit_id, 'bp_type': bp_type,
                'shortage': abs(required_count) - available_count})

    returnValue(missing)


@inlineCallbacks
def _blueprint_invmod_interaction(cursor, player_id, bp_dict):
    """
    This function runs as a transaction within modify_player_item_inventory().
    We call a plpgsql function that modifies inventory levels.
    """

    unit_ref = bp_dict['unit_ref']
    bp_type = bp_dict['bp_type']
    mod_amount = bp_dict['mod_amount']
    result = yield cursor.execute(
        'SELECT modify_plr_blueprint_inventory(%s, %s, %s, %s);',
        (player_id, unit_ref, bp_type, mod_amount))

    returnValue(result.fetchone()[0])


@inlineCallbacks
def modify_player_blueprint_inventory(player_dbref, bp_mods):
    """
    Calls a plpgsql function that upserts into inventories_ownedblueprints to
    modify the player's inventory level for the given blueprint.

    :param str player_dbref: Valid dbref of the player whose inventory
        levels to modify.
    :param list bp_mods: A list of bp modifier dicts, each one representing
        one modification within the transaction.
    :rtype: int
    :returns: The new balance for the modified item.
    """

    player_id = int(player_dbref[1:])
    conn = yield get_db_connection()

    new_levels = []
    for bp_dict in bp_mods:
        try:
            result = yield conn.runInteraction(
                _blueprint_invmod_interaction, player_id, bp_dict)
        except IntegrityError as exc:
            if exc.pgcode == '23514':
                missing_dict = yield check_player_blueprint_levels(
                    player_dbref, bp_mods)
                raise InsufficientInventory(missing_dict)
            else:
                raise

        new_levels.append({
            'unit_ref': bp_dict['unit_ref'], 'bp_type': bp_dict['bp_type'],
            'new_level': result,
        })
    returnValue(new_levels)


@inlineCallbacks
def get_player_blueprint_inventory(player_dbref, unit_ref=None):
    """
    Returns a player's blueprint inventory.

    :param str player_dbref: A valid player dbref.
    :keyword str unit_ref: If we're only returning blueprints for a single
        ref, list it here.
    :rtype: list
    :returns: A list of inventory item dicts.
    """

    owner_id = int(player_dbref[1:])
    query = (
        "SELECT unit_id, bp_type, quantity"
        "  FROM inventories_ownedunitblueprint "
        "  WHERE quantity > 0 AND owner_id=%s"
    )

    qtuple = (owner_id,)

    if unit_ref:
        query += " AND unit_id ILIKE %s "
        qtuple += (unit_ref,)

    query += ' ORDER BY unit_id'
    conn = yield get_db_connection()
    results = yield conn.runQuery(query, qtuple)

    blueprints = OrderedDict()
    for result in results:
        unit_id = result['unit_id']
        bp_type = result['bp_type']
        quantity = result['quantity']
        if unit_id not in blueprints:
            blueprints[unit_id] = {}
        blueprints[unit_id][bp_type] = quantity

    returnValue(blueprints)
