from psycopg2 import IntegrityError
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.inventories.exceptions import \
    InsufficientInventory


@inlineCallbacks
def check_player_item_levels(player_dbref, required_dict):
    """
    Given a dict whose keys are econ items and whose values are integers
    representing how many of said items are required, look through
    the player's inventory and see what (if any) items are missing.

    If certain items are found to be at inadequate levels, said item(s)
    will end up in the returned dict with the value being how many additional
    items are needed.

    :param str player_dbref: The dbref of the player whose inventory to check.
    :param dict required_dict: A dict whose keys are case-sensitive item
        names, and whose values are the required amounts. Required amounts
        should be negative.
    :rtype: dict
    :return: A dict of items that the player needs more of. If they have
        everything, this is an empty dict.
    """

    owner_id = int(player_dbref[1:])
    query = (
        "SELECT item_id, quantity FROM inventories_owneditem "
        "  WHERE quantity > 0 AND owner_id=%s AND item_id = ANY(%s)"
    )

    conn = yield get_db_connection()
    results = yield conn.runQuery(query, (owner_id, required_dict.keys()))
    # These are the matching items in the player's inventory.
    available_dict = {iname: ilevel for iname, ilevel in results}

    missing_dict = {}
    for item_name, required_count in required_dict.items():
        if required_count >= 0:
            continue
        available_count = available_dict.get(item_name, 0)
        if available_count < abs(required_count):
            missing_dict[item_name] = abs(required_count) - available_count

    returnValue(missing_dict)


@inlineCallbacks
def _item_invmod_interaction(cursor, player_id, modded_dict):
    """
    This function runs as a transaction within modify_player_item_inventory().
    We call a plpgsql function that modifies inventory levels.
    """

    for item_name, mod_amount in modded_dict.items():
        yield cursor.execute(
            'SELECT modify_plr_item_inventory(%s, %s, %s);',
            (player_id, item_name, mod_amount))


@inlineCallbacks
def modify_player_item_inventory(player_dbref, modded_dict):
    """
    Calls a plpgsql function that upserts into inventories_owneditem to
    modify the player's inventory level for the given econ item.

    :param str player_dbref: Valid dbref of the player whose inventory
        levels to modify.
    :param dict modded_dict: A dict of items whose inventory levels to
        modify on the player. Negative keys remove items. Positives adds.
    :rtype: int
    :returns: The new balance for the modified item.
    """

    player_id = int(player_dbref[1:])
    conn = yield get_db_connection()
    try:
        yield conn.runInteraction(_item_invmod_interaction, player_id, modded_dict)
    except IntegrityError as exc:
        if exc.pgcode == '23514':
            missing_dict = yield check_player_item_levels(
                player_dbref, modded_dict)
            raise InsufficientInventory(missing_dict)
        else:
            raise


@inlineCallbacks
def get_player_item_inventory(player_dbref, type_filter=None):
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
