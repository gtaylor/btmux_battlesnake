from twisted.internet.defer import inlineCallbacks, returnValue
from battlesnake.plugins.contrib.unit_library.defines import \
    WEIGHT_CLASS_SQL_MAP, UNIT_TYPE_SQL_MAP, \
    UNIT_WCLASS_LIGHT, UNIT_WCLASS_MEDIUM, UNIT_WCLASS_HEAVY, \
    UNIT_WCLASS_ASSAULT, WEIGHT_CLASS_COLOR_MAP

from btmux_template_io.unit import BTMuxUnit
from battlesnake.plugins.contrib.pg_db.api import get_db_connection

from battlesnake.plugins.contrib.unit_library.unit_scanning.db_io import update_unit_in_db, \
    insert_unit_in_db


@inlineCallbacks
def get_library_summary_list(filter_class=None, filter_type=None):
    """
    Returns a dict of unit library info. This can optionally be filtered.

    :keyword str filter_class: One of light, medium, heavy, or assault.
    :keyword str filter_type: One of mech, tank, vtol, or battlesuit.
    :rtype: dict
    :returns: A dict with library summary details included.
    """

    filters = ['is_hidden=False']

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
        'SELECT reference, weight FROM unit_library_unit WHERE {where_clause} '
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


@inlineCallbacks
def get_unit_by_ref(unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve.
    :rtype: btmux_template_io.unit.BTMuxUnit or None
    :returns: A BTMuxUnit instance if a match was found, None if not.
    """

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT unit_library_unit.*, unit_library_manufacturer.name as manufacturer '
        'FROM unit_library_unit '
        'LEFT OUTER JOIN unit_library_manufacturer ON manufacturer_id=unit_library_manufacturer.id '
        'WHERE reference ILIKE %s',
        (unit_ref,)
    )
    for row in results:
        unit = BTMuxUnit()
        unit.reference = row['reference']
        unit.name = row['name']
        unit.unit_type = row['unit_type']
        unit.heatsink_total = row['heatsink_total']
        unit.weight = row['weight']
        unit.max_speed = row['max_speed']
        unit.cargo_space = row['cargo_space']
        unit.cargo_max_ton = row['cargo_max_tonnage']
        unit.base_cost = row['base_cost']
        unit.sections = row['sections']
        unit.specials = set(row['special_tech_raw'].split())
        unit.manufacturer = row['manufacturer']
        returnValue(unit)
    raise ValueError("Invalid ref.")


@inlineCallbacks
def save_unit_to_db(unit, offensive_bv2, defensive_bv2, base_cost, tech_list,
                    payload, build_parts):
    """
    Given a BTMuxUnit instance, save it to the DB. This will either be
    an insert or update, depending on whether the unit is already in the DB.

    :param btmux_template_io.unit.BTMuxUnit unit: The unit to save in the DB.
    :param float offensive_bv2: The in-game calculated offensive battle value 2.
    :param float defensive_bv2: The in-game calculated defensive battle value 2.
    :param int base_cost: The in-game calculated base cost.
    :param set tech_list: A set of special tech in the unit.
    :param dict payload: A dict breaking down the unit's weapons/ammo payload.
    :param dict build_parts: A dict containing the unit's parts list.
    """

    try:
        yield get_unit_by_ref(unit.reference)
        exists = True
    except ValueError:
        exists = False

    if exists:
        update_unit_in_db(
            unit, offensive_bv2, defensive_bv2, base_cost, tech_list,
            payload, build_parts)
    else:
        insert_unit_in_db(
            unit, offensive_bv2, defensive_bv2, base_cost, tech_list,
            payload, build_parts)


def get_weight_class(weight):
    """
    :param int weight: A unit weight (in tons).
    :rtype: str
    :returns: The weight class constant for the given weight.
    """

    if weight < 40:
        return UNIT_WCLASS_LIGHT
    elif weight < 60:
        return UNIT_WCLASS_MEDIUM
    elif weight < 80:
        return UNIT_WCLASS_HEAVY
    else:
        return UNIT_WCLASS_ASSAULT


def get_weight_class_color_for_tonnage(weight):
    """
    :param int weight: A unit weight (in tons).
    :rtype: str
    :returns: The MUX ANSI color code for the given tonnage.
    """

    weight_class = get_weight_class(weight)
    return WEIGHT_CLASS_COLOR_MAP[weight_class]
