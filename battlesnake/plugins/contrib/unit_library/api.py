from twisted.internet.defer import inlineCallbacks, returnValue

from btmux_template_io.unit import BTMuxUnit
from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.unit_library.unit_scanning.db_io import update_unit_in_db, \
    insert_unit_in_db


@inlineCallbacks
def get_unit_by_ref(unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve.
    :rtype: btmux_template_io.unit.BTMuxUnit or None
    :returns: A BTMuxUnit instance if a match was found, None if not.
    """

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT * FROM unit_library_unit WHERE reference=%s',
        (unit_ref,)
    )
    for row in results:
        # TODO: Un-marshal crit sections.
        unit = BTMuxUnit()
        unit.reference = row['reference']
        unit.name = row['name']
        unit.unit_type = row['unit_type']
        unit.weight = row['weight']
        unit.max_speed = row['max_speed']
        unit.unit_tro = row['tro_id']
        unit.cargo_space = row['cargo_space']
        unit.cargo_max_ton = row['cargo_max_tonnage']
        unit.base_cost = row['base_cost']
        returnValue(unit)


@inlineCallbacks
def get_tro_id_from_name(tro_name):
    """
    :param str tro_name: The technical readout name whose ID to look up.
    :rtype: int or None
    :returns: The TRO's ID if a match was found, or None if not.
    """

    if not tro_name:
        returnValue(None)
    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT id FROM unit_library_technicalreadout WHERE name=%s',
        (tro_name,)
    )
    for result in results:
        for row in result:
            returnValue(row)


@inlineCallbacks
def save_unit_to_db(unit, bv, bv2, base_cost, tech_list):
    """
    Given a BTMuxUnit instance, save it to the DB. This will either be
    an insert or update, depending on whether the unit is already in the DB.

    :param btmux_template_io.unit.BTMuxUnit unit: The unit to save in the DB.
    :param int bv: The in-game calculated battle value.
    :param float bv2: The in-game calculated battle value 2.
    :param int base_cost: The in-game calculated base cost.
    :param set tech_list: A set of special tech in the unit.
    """

    exists = yield get_unit_by_ref(unit.reference)
    tro_id = yield get_tro_id_from_name(unit.unit_tro)
    if exists:
        update_unit_in_db(unit, bv, bv2, base_cost, tech_list, tro_id)
    else:
        insert_unit_in_db(unit, bv, bv2, base_cost, tech_list, tro_id)
