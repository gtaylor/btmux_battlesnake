from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def modify_player_inventory(player_dbref, item_name, mod_amount):
    """
    Calls a plpgsql function that upserts into inventories_owneditem to
    modify the player's inventory level for the given econ item.

    :param str player_dbref: Valid dbref of the player whose inventory
        levels to modify.
    :param str item_name: The item name whose inventory level to modify.
    :param int mod_amount: The amount to add (positive number) or remove
        (negative number).
    :rtype: int
    :returns: The new balance for the modified item.
    """

    player_id = int(player_dbref[1:])
    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT modify_player_inventory(%s, %s, %s);',
        (player_id, item_name, mod_amount)
    )
    for result in results:
        for row in result:
            returnValue(row)


@inlineCallbacks
def get_player_inventory(player_dbref, type_filter=None):
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
