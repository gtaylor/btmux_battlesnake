"""
This module contains private functions used to store BTMuxUnit objects
in the DB.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def update_unit_in_db(unit, bv, bv2, base_cost, tech_list, tro_id):
    """
    :param btmux_template_io.unit.BTMuxUnit unit: The unit to save in the DB.
    :param int bv: The in-game calculated battle value.
    :param float bv2: The in-game calculated battle value 2.
    :param int base_cost: The in-game calculated base cost.
    :param set tech_list: A set of special tech in the unit.
    :type tro_id: int or None
    :param tro_id: The unit's TRO's ID or None if no TRO is set.
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
        tro_id,
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

    yield conn.runOperation(query_str, value_tuple)


@inlineCallbacks
def insert_unit_in_db(unit, bv, bv2, base_cost, tech_list, tro_id):
    """
    :param btmux_template_io.unit.BTMuxUnit unit: The unit to save in the DB.
    :param int bv: The in-game calculated battle value.
    :param float bv2: The in-game calculated battle value 2.
    :param int base_cost: The in-game calculated base cost.
    :param set tech_list: A set of special tech in the unit.
    :type tro_id: int or None
    :param tro_id: The unit's TRO's ID or None if no TRO is set.
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
        tro_id,
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
