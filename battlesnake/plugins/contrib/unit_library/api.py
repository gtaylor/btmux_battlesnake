from psycopg2._psycopg import DataError
from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def get_unit_by_ref(unit_ref):
    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT * FROM unit_library_unit WHERE reference=%s',
        (unit_ref,)
    )
    # TODO: Unmarshal the unit here
    returnValue(results)


@inlineCallbacks
def save_unit_to_db(unit, bv, bv2, base_cost, tech_list):
    try:
        exists = yield get_unit_by_ref(unit.reference)
    except DataError:
        exists = False

    print "EXISTS", exists
    if exists:
        _update_unit_in_db(unit, bv, bv2, base_cost, tech_list)
    else:
        _insert_unit_in_db(unit, bv, bv2, base_cost, tech_list)


@inlineCallbacks
def _insert_unit_in_db(unit, bv, bv2, base_cost, tech_list):
    """
    :param btmux_template_io.unit.BTMuxUnit unit:
    """

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO unit_library_unit'
        '  (reference, name, unit_type, unit_move_type, weight, max_speed,'
        '   tro_id, engine_size, armor_total, internals_total, heatsink_total,'
        '   battle_value, battle_value2, cargo_space, cargo_max_tonnage,'
        '   jumpjet_range, base_cost, special_tech)'
        '  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,'
        '   %s, %s, %s)'
    )
    value_tuple = (
        unit.reference,
        unit.name,
        unit.unit_type,
        unit.unit_move_type,
        unit.weight,
        unit.max_speed,
        None, # TRO ID
        unit.engine_size,
        unit.armor_total,
        unit.internals_total,
        unit.heatsink_total,
        bv,
        bv2,
        unit.cargo_space,
        unit.cargo_max_ton or 0,
        unit.jumpjet_range,
        base_cost,
        ' '.join(list(tech_list)),
    )

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def _update_unit_in_db(unit, bv, bv2, base_cost, tech_list):
    """
    :param btmux_template_io.unit.BTMuxUnit unit:
    """

    conn = yield get_db_connection()
    query_str = (
        'UPDATE unit_library_unit SET'
        '  name=%s,'
        '  unit_type=%s,'
        '  unit_move_type=%s,'
        '  weight=%s,'
        '  max_speed=%s,'
        '  tro_id=%s,'
        '  engine_size=%s,'
        '  armor_total=%s,'
        '  internals_total=%s,'
        '  heatsink_total=%s,'
        '  battle_value=%s,'
        '  battle_value2=%s,'
        '  cargo_space=%s,'
        '  cargo_max_tonnage=%s,'
        '  jumpjet_range=%s,'
        '  base_cost=%s,'
        '  special_tech=%s'
        ' WHERE reference=%s'
    )
    value_tuple = (
        unit.name,
        unit.unit_type,
        unit.unit_move_type,
        unit.weight,
        unit.max_speed,
        None, # TRO ID
        unit.engine_size,
        unit.armor_total,
        unit.internals_total,
        unit.heatsink_total,
        bv,
        bv2,
        unit.cargo_space,
        unit.cargo_max_ton or 0,
        unit.jumpjet_range,
        base_cost,
        ' '.join(list(tech_list)),
        unit.reference,
    )

    print query_str % value_tuple

    yield conn.runOperation(query_str, value_tuple)
