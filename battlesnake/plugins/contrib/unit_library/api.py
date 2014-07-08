from twisted.internet.defer import inlineCallbacks, returnValue

from btmux_template_io.unit import BTMuxUnit
from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.unit_library.unit_scanning.db_io import update_unit_in_db, \
    insert_unit_in_db


@inlineCallbacks
def get_library_summary_list(filter_class=None, filter_type=None):
    """
    Returns a dict of unit library info. This can optionally be filtered.

    :keyword str filter_class: One of light, mediu, heavy, or assault.
    :keyword str filter_type: One of mech, tank, vtol, or battlesuit.
    :rtype: dict
    :returns: A dict with library summary details included.
    """

    query = (
        'SELECT reference, weight FROM unit_library_unit WHERE '
        '  is_hidden=False '
    )

    if filter_class:
        filter_class = filter_class.lower()
        query += 'AND '
        if filter_class == 'light':
            query += 'weight < 40'
        elif filter_class == 'medium':
            query += 'weight >= 40 AND weight < 60'
        elif filter_class == 'heavy':
            query += 'weight >= 60 AND weight < 80'
        elif filter_class == 'assault':
            query += 'weight >= 80'
        else:
            query += 'true'

    if filter_type:
        filter_type = filter_type.lower()
        if filter_type == 'mech':
            unit_type = 'Mech'
        elif filter_type == 'tank':
            unit_type = 'Vehicle'
        elif filter_type == 'vtol':
            unit_type = 'VTOL'
        elif filter_type == 'battlesuit':
            unit_type = 'Battlesuit'
        else:
            unit_type = None

        if unit_type:
            query += "AND unit_type = '%s'" % unit_type

    query += ' ORDER BY reference'
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


@inlineCallbacks
def get_unit_by_ref(unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve.
    :rtype: btmux_template_io.unit.BTMuxUnit or None
    :returns: A BTMuxUnit instance if a match was found, None if not.
    """

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT * FROM unit_library_unit WHERE reference ILIKE %s',
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
        unit.sections = row['sections']
        unit.specials = set(row['special_tech_raw'].split())
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
def save_unit_to_db(unit, bv, offensive_bv2, defensive_bv2, base_cost, tech_list,
                    payload, build_parts):
    """
    Given a BTMuxUnit instance, save it to the DB. This will either be
    an insert or update, depending on whether the unit is already in the DB.

    :param btmux_template_io.unit.BTMuxUnit unit: The unit to save in the DB.
    :param int bv: The in-game calculated battle value.
    :param float offensive_bv2: The in-game calculated offensive battle value 2.
    :param float defensive_bv2: The in-game calculated defensive battle value 2.
    :param int base_cost: The in-game calculated base cost.
    :param set tech_list: A set of special tech in the unit.
    :param dict payload: A dict breaking down the unit's weapons/ammo payload.
    :param dict build_parts: A dict containing the unit's parts list.
    """

    exists = yield get_unit_by_ref(unit.reference)
    tro_id = yield get_tro_id_from_name(unit.unit_tro)
    if exists:
        update_unit_in_db(
            unit, bv, offensive_bv2, defensive_bv2, base_cost, tech_list,
            tro_id, payload, build_parts)
    else:
        insert_unit_in_db(
            unit, bv, offensive_bv2, defensive_bv2, base_cost, tech_list,
            tro_id, payload, build_parts)
