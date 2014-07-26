"""
The API for interacting with arena-related data in the DB.
"""

import datetime

from psycopg2.extras import Json
from twisted.internet.defer import inlineCallbacks, returnValue
from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_STAGING
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF

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
        GAME_STATE_STAGING,
        puppet.difficulty_level,
        0,
        Json({}),
        datetime.datetime.now()
    )
    result = yield conn.runQuery(query_str, value_tuple)
    # The newly inserted match's ID.
    returnValue(result[0][0])


@inlineCallbacks
def update_match_game_state_in_db(puppet):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_match SET'
        '  game_state=%s '
        ' WHERE id=%s'
    )
    value_tuple = (
        puppet.game_state,
        puppet.match_id,
    )

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def update_match_difficulty_in_db(puppet):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_match SET'
        '  difficulty_level=%s '
        ' WHERE id=%s'
    )
    value_tuple = (
        puppet.difficulty_level,
        puppet.match_id,
    )

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def update_highest_wave_in_db(puppet):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_match SET'
        '  highest_wave_completed=%s '
        ' WHERE id=%s'
    )
    value_tuple = (
        puppet.current_wave,
        puppet.match_id,
    )

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def mark_match_as_finished_in_db(puppet):
    """

    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE arena_match SET'
        '  finished_time=%s'
        ' WHERE id=%s'
    )
    value_tuple = (
        datetime.datetime.now(),
        puppet.match_id
    )

    yield conn.runOperation(query_str, value_tuple)


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
def insert_wave_in_db(puppet, spawned_units):
    """
    :param list spawned_units: A list of tuples describing the units that were
        spawned as part of the wave.
    """

    leader_id = int(puppet.leader_dbref[1:])
    conn = yield get_db_connection()

    # Insert a new Wave row.
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
    wave_id = result[0][0]

    participant_query_str = (
        'INSERT INTO arena_participant'
        '  (wave_id, unit_id, pilot_id, faction_id, unit_dbref)'
        '  VALUES (%s, %s, %s, %s, %s)'
    )

    # No record all participants.
    units = puppet.list_defending_units()
    for unit in units:
        value_tuple = (
            wave_id,
            unit.unit_ref,
            int(unit.pilot_dbref[1:]) if not unit.is_ai else None,
            int(unit.faction_dbref[1:]),
            int(unit.dbref[1:]),
        )
        yield conn.runOperation(participant_query_str, value_tuple)

    for unit in spawned_units:
        unit_ref, unit_dbref = unit
        value_tuple = (
            wave_id,
            unit_ref,
            None,
            int(ATTACKER_FACTION_DBREF[1:]),
            int(unit_dbref[1:]),
        )
        yield conn.runOperation(participant_query_str, value_tuple)

    returnValue(wave_id)


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


@inlineCallbacks
def _get_match_current_wave_id(puppet):
    """
    """

    match_id = puppet.match_id
    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT id FROM arena_wave WHERE match_id=%s ORDER BY id DESC LIMIT 1',
        (match_id,)
    )
    for result in results:
        for row in result:
            returnValue(row)


@inlineCallbacks
def get_participant_id_from_db(wave_id, unit_dbref):
    """
    :param int wave_id: The wave's unique ID.
    :param str unit_dbref: The unit's full dbref.
    :rtype: int or None
    :returns: The participant's ID if a match was found, or None if not.
    """

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT id FROM arena_participant WHERE wave_id=%s AND unit_dbref=%s',
        (int(wave_id), int(unit_dbref[1:]))
    )
    for result in results:
        for row in result:
            returnValue(row)


@inlineCallbacks
def record_kill_in_db(puppet, victim_dbref, killer_dbref):
    """

    """

    wave_id = yield _get_match_current_wave_id(puppet)
    if not wave_id:
        print "Kill reported, but no wave_id match found in DB."
        returnValue(None)
    victim_id = yield get_participant_id_from_db(wave_id, victim_dbref)
    if not victim_id:
        print "Unable to find victim: wave %d, victim %s" % (wave_id, victim_dbref)
        returnValue(None)
    killer_id = yield get_participant_id_from_db(wave_id, killer_dbref)
    if not killer_id:
        print "Unable to find killer: wave %d, killer %s" % (wave_id, killer_dbref)
        returnValue(None)

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO arena_kill'
        '  (wave_id, killer_id, victim_id)'
        '  VALUES (%s, %s, %s)'
        ' RETURNING id'
    )
    value_tuple = (
        wave_id,
        killer_id,
        victim_id,
    )
    result = yield conn.runQuery(query_str, value_tuple)
    # The newly inserted kill's ID.
    kill_id = result[0][0]

    # Now update the Participant record to reflect their untimely death.
    query_str = (
        'UPDATE arena_participant SET'
        '  death_id=%s'
        ' WHERE id=%s'
    )
    value_tuple = (
        kill_id,
        victim_id,
    )
    yield conn.runOperation(query_str, value_tuple)

    returnValue(kill_id)
