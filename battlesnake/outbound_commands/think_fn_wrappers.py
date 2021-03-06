"""
Functions wrappers using the 'think' command.
"""

import inspect
import itertools

from twisted.internet.defer import inlineCallbacks, returnValue
from battlesnake.core.utils import add_escaping_percent_sequences

from battlesnake.outbound_commands import mux_commands
from btmux_template_io.item_table import WEAPON_TYPE_IDS


def create(protocol, name, otype='r'):
    """
    :param str name: The new object will take this name.
    :param str otype: One of: r (Room), t (Thing), or e (Exit).
    :rtype: defer.Deferred
    :returns: A deferred that will fire with the new object's dbref.
    """

    think_str = "[create({name},1,{otype})]".format(
        name=name, otype=otype,
    )
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def tel(protocol, obj, dest):
    """
    :param str obj: The dbref of the object to teleport.
    :param str dest: The dbref of the teleportation destination.
    :rtype: defer.Deferred
    """

    think_str = "[tel({obj},{dest})]".format(obj=obj, dest=dest)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def pemit(protocol, objects, message):
    """
    :param list objects: A list of dbrefs to pemit() to.
    :param str message: The message to pemit().
    :rtype: defer.Deferred
    :returns: A deferred that will fire with the new object's dbref.
    """

    if isinstance(objects, list):
        obj_dbrefs = ' '.join(objects)
    else:
        obj_dbrefs = objects
    think_str = "[pemit({obj_dbrefs},{message})]".format(
        obj_dbrefs=obj_dbrefs, message=message,
    )
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def cemit(protocol, channel, message):
    """
    :param str channel: A channel name to emit to.
    :param str message: The message to cemit().
    """

    think_str = "[cemit({channel},{message})]".format(
        channel=channel, message=message,
    )
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


@inlineCallbacks
def set_attrs(protocol, obj, attr_dict, iter_delim='|'):
    """
    Uses set() to set one or more attributes on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param dict attr_dict: A dict of string key/vals to set on the object.
        If one of your values contains the default ``iter_delim`` (the
        pip character), things could get messy. Choose your delimiter
        wisely!
    """

    if not attr_dict:
        return
    if len(attr_dict) == 1:
        items = attr_dict.items()
        key, val = items[0]
        think_str = "[set({obj},{key}:{val})]".format(
            obj=obj, key=key, val=val,
        )
        yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())

    iter_vals = []
    for key, val in attr_dict.items():
        iter_vals.append("{key}:{val}".format(
            key=key, val=val, iter_delim=iter_delim))
    iter_vals_str = '|'.join(iter_vals)
    think_str = "[iter({iter_vals},[set({obj},##)],{iter_delim})]".format(
        iter_vals=iter_vals_str, obj=obj, iter_delim=iter_delim)
    yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def get(protocol, obj, attr_name):
    """
    Retrieves an attribute from an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str attr_name: The name of the attribute to retrieve.
    """

    think_str = "[get({obj}/{attr_name})]".format(
        obj=obj, attr_name=attr_name)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


@inlineCallbacks
def get_attrs(protocol, obj, attr_list, attr_delim='@&~'):
    """
    Retrieves multiple attributes from an object in one shot. More efficient
    than multiple calls to get().

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param list attr_list: A list of attribute key names to retrieve.
    :keyword str attr_delim: This delimeter breaks up the get() values in
        the response.
    """

    key_iter_str = '|'.join(attr_list)
    think_str = "[iter({key_iter_str},[get({obj}/##)]{attr_delim},|)]".format(
        key_iter_str=key_iter_str, obj=obj, attr_delim=attr_delim)
    result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    vals = result.split(attr_delim)
    combined = itertools.izip(attr_list, vals)
    returnValue({k: v.strip() for k, v in combined})


def name(protocol, obj):
    """
    Retrieves an object's name.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    """

    think_str = "[name({obj})]".format(obj=obj)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def set_flags(protocol, obj, flags):
    """
    Uses set() to set (or unset) flags on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param list flags: A list of flag strings to be set.
    """

    if not flags:
        return

    iter_vals = ' '.join(flags)
    think_str = "[iter({iter_vals},[set({obj},##)])]".format(
        iter_vals=iter_vals, obj=obj)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def teleport(protocol, obj, dest_obj):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str dest_obj: A valid MUX object string for the destination.
    :rtype: defer.Deferred
    """

    think_str = "[tel({obj},{dest_obj})]".format(
        obj=obj, dest_obj=dest_obj)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btloadmech(protocol, obj, unit_ref):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str unit_ref: The reference to load on this unit.
    :rtype: defer.Deferred
    """

    think_str = "[btloadmech({obj},{unit_ref})]".format(
        obj=obj, unit_ref=unit_ref)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btloadmap(protocol, obj, map_filename):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str map_filename: The map filename to load.
    :rtype: defer.Deferred
    """

    think_str = "[btloadmap({obj},{map_filename})]".format(
        obj=obj, map_filename=map_filename)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btsetmaphex(protocol, obj, x, y, terrain, elev):
    """
    :param str obj: A valid map object string. 'here', a dbref, etc.
    :param int x: The X coord to set.
    :param int y: The Y coord to set.
    :param str terrain: The terrain symbol to set ('.' for clear).
    :param int elev: The elevation of the hex.
    :rtype: defer.Deferred
    """

    escaped_terrain = add_escaping_percent_sequences(terrain)
    think_str = "[btsetmaphex({obj},{x},{y},{terrain},{elev})]".format(
        obj=obj, x=x, y=y, terrain=escaped_terrain, elev=elev)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btsetmaphex_line(protocol, obj, y, terrain_line, elev_line):
    """
    If you need to set a bunch of hexes at a time, it's much faster to
    do an entire row of hexes at once than to do them all individually.
    Note that you will eventually hit the input buffer limit if your
    Y line is too wide. We should probably eventually handle that here.

    :param str obj: A valid map object string. 'here', a dbref, etc.
    :param int y: The Y line whose hexes to set.
    :param list terrain_line: A list of terrain values for the Y line.
    :param list elev_line: A list of elevation values for the Y line.
    :rtype: defer.Deferred
    """

    buf = ""
    for x, _ in enumerate(terrain_line):
        terrain = terrain_line[x]
        elev = elev_line[x]
        escaped_terrain = add_escaping_percent_sequences(terrain)
        buf += "[btsetmaphex({obj},{x},{y},{terrain},{elev})]".format(
            obj=obj, x=x, y=y, terrain=escaped_terrain, elev=elev)
    return mux_commands.think(protocol, buf, debug_info=inspect.stack())


def btsetxy(protocol, obj, map_obj, unit_x, unit_y, unit_z=''):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str map_obj: A valid MUX object string for the map to place the
        unit on.
    :param int unit_x: The X coord to set the unit to.
    :param int unit_y: The Y coord to set the unit to.
    :param int unit_y: The Z coord to set the unit to.
    :rtype: defer.Deferred
    """

    if unit_z:
        think_str = "[btsetxy({obj},{map_obj},{unit_x},{unit_y},{unit_z})]".format(
            obj=obj, map_obj=map_obj, unit_x=unit_x, unit_y=unit_y, unit_z=unit_z)
    else:
        think_str = "[btsetxy({obj},{map_obj},{unit_x},{unit_y})]".format(
            obj=obj, map_obj=map_obj, unit_x=unit_x, unit_y=unit_y)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btsetxcodevalue(protocol, obj, key, val):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str key: The XCODE key to set.
    :param val: The XCODE val to set on the key.
    :rtype: defer.Deferred
    """

    think_str = "[btsetxcodevalue({obj},{key},{val})]".format(
        obj=obj, key=key, val=val)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btsetcharvalue(protocol, obj, skill_or_attrib, val, mode):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str skill_or_attrib: A skill or character attribute name.
    :param int val: The value to set the skill or attribute to.
    :param int mode: See mode values below.
    :rtype: defer.Deferred

    Valid modes:

    * 0 - set the actual value of <skill/attribute> to <value>
    * 1 - set the BTH of <skill> to <value> (increasing the skill level to
          the necessary extent)
    * 2 - adds <value> to the XP amount of <skill/attribute>
    * 3 - set XP amount of <skill/attribute> to <value>
    """

    think_str = "[btsetcharvalue({obj},{skill_or_attrib},{val},{mode})]".format(
        obj=obj, skill_or_attrib=skill_or_attrib, val=val, mode=mode)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btgetxcodevalue(protocol, obj, key):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str key: The XCODE key to retrieve the value for.
    :rtype: defer.Deferred
    """

    think_str = "[btgetxcodevalue({obj},{key})]".format(
        obj=obj, key=key)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


def btgetxcodevalue_ref(protocol, unit_ref, key):
    """
    :param str unit_ref: The unit reference to retrieve values for.
    :param str key: The XCODE key to retrieve the value for.
    :rtype: defer.Deferred
    """

    think_str = "[btgetxcodevalue_ref({unit_ref},{key})]".format(
        unit_ref=unit_ref, key=key)
    return mux_commands.think(protocol, think_str, debug_info=inspect.stack())


@inlineCallbacks
def btgetbv2_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve the BV2 for.
    :rtype: float
    """

    think_str = "[btgetbv2_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(float(func_result))


@inlineCallbacks
def btgetobv_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve the offensive
        BV2 for.
    :rtype: float
    """

    think_str = "[btgetobv_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(float(func_result))


@inlineCallbacks
def btgetdbv_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to retrieve the defensive
        BV2 for.
    :rtype: float
    """

    think_str = "[btgetdbv_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(float(func_result))


@inlineCallbacks
def btfasabasecost_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to calculate a base cost for.
    :rtype: int
    """

    think_str = "[btfasabasecost_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(max(0, int(func_result)))


@inlineCallbacks
def btdesignex(protocol, unit_ref):
    """
    :param str unit_ref: A unit reference to check.
    :rtype: bool
    :returns: True if the reference exists, False if not.
    """

    think_str = "[btdesignex({unit_ref})]".format(
        unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(func_result == '1')


@inlineCallbacks
def bttechlist_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to get the tech list for.
    :rtype: list
    """

    think_str = "[bttechlist_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(set(func_result.split()))


@inlineCallbacks
def btpayload_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to get the payload for.
    :rtype: list
    """

    think_str = "[btpayload_ref({unit_ref})]".format(unit_ref=unit_ref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    retval = {}
    if not func_result:
        returnValue(retval)
    weapon_split = func_result.split('|')
    for weapon_pair in weapon_split:
        weapon, quantity = weapon_pair.split(':')
        retval[weapon] = quantity
    returnValue(retval)


@inlineCallbacks
def btweapstat(protocol, weapon):
    """
    Given a weapon, return a dict of weapon stats.

    :param str weapon: The weapon name to get the stats for.
    :rtype: dict
    :returns: A dict of weapon stats.
    """

    weapstat_str = "[btweapstat({weapon},{field})]"
    fields = [
        'VRT', 'TYPE', 'HEAT', 'DAMAGE', 'MIN', 'SR', 'MR', 'LR', 'CRIT',
        'AMMO', 'WEIGHT', 'BV'
    ]
    think_list = []
    for field in fields:
        think_list.append(weapstat_str.format(field=field, weapon=weapon))
    think_str = '^'.join(think_list)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    vrt, weap_type, heat, damage, min_range, short_range, medium_range, \
        long_range, crits, ammo_pt, weight, bv = func_result.split('^')

    weap_type = WEAPON_TYPE_IDS[weap_type]
    if weap_type not in ['Missile', 'Ballistic', 'Artillery']:
        ammo_pt = None
    else:
        ammo_pt = int(ammo_pt)
    retval = {
        'vrt': int(vrt),
        'weapon_type': weap_type,
        'heat': int(heat),
        'damage': int(damage),
        'min_range': int(min_range),
        'short_range': int(short_range),
        'medium_range': int(medium_range),
        'long_range': int(long_range),
        'crits': int(crits),
        'ammo_count': ammo_pt,
        'weight': float(weight) / 100.0,
        'bv': int(bv),
    }
    returnValue(retval)


def _parse_partslist(pl_output):
    """
    Given the output of btpartslist() or btpartslist_ref(), parse it and
    split it back out as a dict.

    :param str pl_output: The output of btpartslist() or btpartslist_ref().
    :rtype: dict
    :returns: A dict of parts.
    """

    retval = {}
    if not pl_output:
        returnValue(retval)
    part_split = pl_output.split('|')
    for part_pair in part_split:
        if not part_pair:
            continue
        part, quantity = part_pair.split(':')
        retval[part] = int(quantity)
    return retval


@inlineCallbacks
def btunitpartslist_ref(protocol, unit_ref):
    """
    :param str unit_ref: The unit reference to get the parts list for.
    :rtype: list
    """

    think_str = "[btunitpartslist_ref({unit_ref})]".format(unit_ref=unit_ref)
    pl_output = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(_parse_partslist(pl_output))


@inlineCallbacks
def btunitpartslist(protocol, obj):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :rtype: list
    """

    think_str = "[btunitpartslist({obj})]".format(obj=obj)
    pl_output = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    returnValue(_parse_partslist(pl_output))


@inlineCallbacks
def get_map_dimensions(protocol, map_dbref):
    """
    :param str map_dbref: A valid MAP dbref.
    :rtype: tuple
    :returns: A tuple in the form of (width, height).
    """

    think_str = "[btgetxcodevalue({map_dbref}, mapwidth)] [btgetxcodevalue({map_dbref}, mapheight)]".format(
        map_dbref=map_dbref)
    func_result = yield mux_commands.think(protocol, think_str, debug_info=inspect.stack())
    coords = func_result.split()
    returnValue((int(coords[0]), int(coords[1])))
