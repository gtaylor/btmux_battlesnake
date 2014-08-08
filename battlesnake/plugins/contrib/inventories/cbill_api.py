from twisted.internet.defer import inlineCallbacks, returnValue

from psycopg2 import IntegrityError

from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.inventories.exceptions import \
    InsufficientCbills


@inlineCallbacks
def mod_player_cbill_balance(player_dbref, mod_amount):
    """
    Modifies a player's cbill balance.

    :param str player_dbref: A valid player dbref.
    :keyword int mod_amount: A positive number adds to the player's balance,
        while a negative number subtracts from it.
    :rtype: int
    :returns: The player's new balance.
    """

    player_id = int(player_dbref[1:])
    query = (
        "UPDATE accounts_sosuser SET cbill_balance=cbill_balance + %s "
        "  WHERE id=%s RETURNING cbill_balance"
    )
    values = (mod_amount, player_id)

    conn = yield get_db_connection()

    try:
        results = yield conn.runQuery(query, values)
    except IntegrityError as exc:
        if exc.pgcode == '23514':
            raise InsufficientCbills()
        else:
            raise

    returnValue(results)
