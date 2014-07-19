"""
The API for interacting with arena-related data in the DB.
"""

import datetime

from psycopg2.extras import Json
from twisted.internet.defer import inlineCallbacks

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def insert_match_in_db(puppet):
    """

    """

    arena_id = int(puppet.dbref[1:])
    creator_id = int(puppet.creator_dbref[1:])

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO arena_match'
        '  (arena_id, creator_id, game_mode, game_state, difficulty_level,'
        '   highest_wave_completed, mode_specific_data, created_time)'
        '  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    )
    value_tuple = (
        arena_id,
        creator_id,
        'wave',
        'staging',
        puppet.difficulty_level,
        0,
        Json({}),
        datetime.datetime.now()
    )
    yield conn.runOperation(query_str, value_tuple)
