"""
Functions wrappers using the 'think' command.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import mux_commands


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
    return mux_commands.think(protocol, think_str)


def set_attrs(protocol, obj, attr_dict):
    """
    Uses set() to set one or more attributes on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param dict attr_dict: A dict of string key/vals to set on the object.
    """

    if not attr_dict:
        return
    if len(attr_dict) == 1:
        items = attr_dict.items()
        key, val = items[0]
        think_str = "[set({obj},{key}:{val})]".format(
            obj=obj, key=key, val=val,
        )
        return mux_commands.think(protocol, think_str)

    iter_vals = ""
    for key, val in attr_dict.items():
        iter_vals += "{key}:{val} ".format(key=key, val=val)
    think_str = "[iter({iter_vals},[set({obj},##)])]".format(
        iter_vals=iter_vals, obj=obj)
    return mux_commands.think(protocol, think_str, return_output=False)


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
    return mux_commands.think(protocol, think_str)


def teleport(protocol, obj, dest_obj):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str dest_obj: A valid MUX object string for the destination.
    :rtype: defer.Deferred
    """

    think_str = "[tel({obj},{dest_obj})]".format(
        obj=obj, dest_obj=dest_obj)
    return mux_commands.think(protocol, think_str, return_output=False)


def btloadmech(protocol, obj, unit_ref):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str unit_ref: The reference to load on this unit.
    :rtype: defer.Deferred
    """

    think_str = "[btloadmech({obj},{unit_ref})]".format(
        obj=obj, unit_ref=unit_ref)
    return mux_commands.think(protocol, think_str, return_output=False)


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

    think_str = "[btsetxy({obj},{map_obj},{unit_x},{unit_z})]".format(
        obj=obj, map_obj=map_obj, unit_x=unit_x, unit_y=unit_y, unit_z=unit_z)
    return mux_commands.think(protocol, think_str, return_output=False)


def btsetxcodevalue(protocol, obj, key, val):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str key: The XCODE key to set.
    :param val: The XCODE val to set on the key.
    :rtype: defer.Deferred
    """

    think_str = "[btsetxcodevalue({obj},{key},{val})]".format(
        obj=obj, key=key, val=val)
    return mux_commands.think(protocol, think_str, return_output=False)


def btgetxcodevalue(protocol, obj, key):
    """
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str key: The XCODE key to retrieve the value for.
    :rtype: defer.Deferred
    """

    think_str = "[btgetxcodevalue({obj},{key})]".format(
        obj=obj, key=key)
    return mux_commands.think(protocol, think_str)
