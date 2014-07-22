"""
The API for interacting with arena-related data in the DB.
"""

import datetime

from psycopg2.extras import Json
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def insert_match_in_db(puppet):
    """

    """

    creator_id = int(puppet.creator_dbref[1:])

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO arena_match'
        '  (arena_id, creator_id, game_mode, game_state, difficulty_level,'
        '   highest_wave_completed, mode_specific_data, created_time)'
        '  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        ' RETURNING id'
    )
    value_tuple = (
        puppet.id,
        creator_id,
        'wave',
        'staging',
        puppet.difficulty_level,
        0,
        Json({}),
        datetime.datetime.now()
    )
    result = yield conn.runQuery(query_str, value_tuple)
    # The newly inserted match's ID.
    returnValue(result[0][0])


@inlineCallbacks
def mark_match_as_destroyed_in_db(puppet):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_match SET'
        '  destroyed_time=%s'
        ' WHERE id=%s'
    )
    value_tuple = (
        datetime.datetime.now(),
        puppet.match_id
    )

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def insert_wave_in_db(puppet):
    """

    """

    leader_id = int(puppet.leader_dbref[1:])

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO arena_wave'
        '  (match_id, wave_number, leader_id, mode_specific_data, start_time,'
        '   was_successfully_completed)'
        '  VALUES (%s, %s, %s, %s, %s, %s)'
        ' RETURNING id'
    )
    value_tuple = (
        puppet.match_id,
        puppet.current_wave,
        leader_id,
        Json({}),
        datetime.datetime.now(),
        False,
    )
    result = yield conn.runQuery(query_str, value_tuple)
    # The newly inserted match's ID.
    returnValue(result[0][0])


@inlineCallbacks
def mark_wave_as_finished_in_db(puppet, was_completed):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_wave SET'
        '  finished_time=%s,'
        '  was_successfully_completed=%s'
        ' WHERE match_id=%s AND wave_number=%s'
    )
    value_tuple = (
        datetime.datetime.now(),
        was_completed,
        puppet.match_id,
        puppet.current_wave,
    )

    yield conn.runOperation(query_str, value_tuple)
