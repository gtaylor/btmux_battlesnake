from psycopg2 import IntegrityError
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.pg_db.api import get_db_connection
from battlesnake.plugins.contrib.unit_library.defines import \
    WEIGHT_CLASS_SQL_MAP, UNIT_TYPE_SQL_MAP


@inlineCallbacks
def get_player_unit_summary_list(player_dbref, filter_class=None,
                                 filter_type=None):
    """
    Returns a dict of unit inventory info for a player. This can optionally
    be filtered.

    :param str player_dbref: The dbref of the player whose
        unit inventory to retrieve.
    :keyword str filter_class: One of light, medium, heavy, or assault.
    :keyword str filter_type: One of mech, tank, vtol, or battlesuit.
    :rtype: dict
    :returns: A dict with library summary details included.
    """

    player_id = int(player_dbref[1:])
    filters = ['owned.owner_id=%d' % player_id]

    if filter_class:
        filter_class = filter_class.lower()
        filter_sql = WEIGHT_CLASS_SQL_MAP.get(filter_class, None)
        if filter_sql:
            filters.append(filter_sql)

    if filter_type:
        filter_type = filter_type.lower()
        filter_sql = UNIT_TYPE_SQL_MAP.get(filter_type, None)
        if filter_sql:
            filters.append(filter_sql)

    where_clause = ' AND '.join(filters)

    query = (
        'SELECT '
        ' owned.obtained_time, lib.reference, lib.weight '
        'FROM inventories_ownedunit AS owned '
        'LEFT OUTER JOIN unit_library_unit AS lib ON owned.unit_id=lib.reference '
        'WHERE {where_clause} '
        'ORDER BY reference'.format(
            where_clause=where_clause))
    conn = yield get_db_connection()
    results = yield conn.runQuery(query)

    retval = {
        'refs': []
    }
    for row in results:
        udict = {
            'reference': row['reference'],
            'weight': row['weight'],
        }
        retval['refs'].append(udict)

    returnValue(retval)
