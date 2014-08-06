from psycopg2 import IntegrityError
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.inventories.exceptions import \
    InsufficientInventory


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
def get_player_blueprint_inventory(player_dbref, type_filter=None):
    """
    Filters, sorts, and returns a player's inventory.

    :param str player_dbref: A valid player dbref.
    :keyword str type_filter: One of: all, part, melee_weapon, weapon, commodity.
    :rtype: list
    :returns: A list of inventory item dicts.
    """

    owner_id = int(player_dbref[1:])
    query = (
        "SELECT item_id, quantity, econ_item.item_type AS item_type"
        "  FROM inventories_owneditem "
        "  INNER JOIN econ_item ON inventories_owneditem.item_id = econ_item.name"
        "  WHERE quantity > 0 AND owner_id=%d" % owner_id
    )

    if type_filter:
        query += " AND item_type='%s' " % type_filter

    query += ' ORDER BY item_id'
    conn = yield get_db_connection()
    results = yield conn.runQuery(query)

    returnValue(results)
