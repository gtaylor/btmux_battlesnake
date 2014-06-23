from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.plugins.contrib.unit_spawning.signals import on_unit_spawned
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def create_unit(protocol, unit_ref, map_dbref, faction,
                unit_x, unit_y, unit_z='', pilot_dbref=None):
    """
    Creates a new unit on the given map at the specified coordinates.

    :param BattlesnakeTelnetProtocol protocol:
    :param str unit_ref: The unit ref to load.
    :param str map_dbref: A MUX object string for the map.
    :param Faction faction: A valid Faction instance.
    :param int unit_x: The X coord to place the unit on the map.
    :param int unit_y: The Y coord to place the unit on the map.
    :keyword int unit_z: The Z coord to place the unit on the map.
    :keyword str pilot_dbref: The dbref of the pilot for this unit.
    :rtype: defer.Deferred
    :returns: A Deferred whose callback value will be the dbref of
        the newly created unit.
    """

    p = protocol
    # The unit isn't far enough along to be given a spiffy name yet. Give it
    # a temporary BS name.
    unit_name = "UnitBeingCreated"
    unit_dbref = yield think_fn_wrappers.create(p, unit_name, otype='t')
    # Get the name of the ref from the unit's mechname XCODE value.
    unit_name = yield think_fn_wrappers.btgetxcodevalue_ref(
        p, unit_ref, 'mechname')

    mux_commands.parent(p, unit_dbref, settings['unit_spawning']['unit_parent_dbref'])
    mux_commands.lock(p, unit_dbref, unit_dbref)
    mux_commands.lock(p, unit_dbref, 'ELOCK/1', whichlock='enter')
    mux_commands.lock(p, unit_dbref, 'LLOCK/1', whichlock='leave')
    mux_commands.lock(p, unit_dbref, 'ULOCK/1', whichlock='use')
    mux_commands.link(protocol, unit_dbref, map_dbref)
    unit_attrs = {
        'Mechtype': unit_ref,
        'Mechname': unit_name,
        'FACTION': faction.dbref,
        'Xtype': 'MECH',
    }
    if pilot_dbref:
        unit_attrs['Pilot'] = pilot_dbref
    yield think_fn_wrappers.set_attrs(protocol, unit_dbref, unit_attrs)

    yield think_fn_wrappers.teleport(protocol, unit_dbref, map_dbref)
    flags = ['INHERIT', 'IN_CHARACTER', 'XCODE', 'ENTER_OK', 'OPAQUE', 'QUIET']
    # At this point, the XCODE flag is set, so we're ready to rock.
    yield think_fn_wrappers.set_flags(protocol, unit_dbref, flags)

    # The unit now has its ref loaded, but is still not on a map.
    yield think_fn_wrappers.btloadmech(p, unit_dbref, unit_ref)
    yield think_fn_wrappers.btsetxcodevalue(p, unit_dbref, 'team', faction.team_num)
    # Mechname is what shows up on 'contacts', so update it to contain
    # the ref's mechname.
    yield think_fn_wrappers.set_attrs(p, unit_dbref, {'Mechname': unit_name})
    new_obj_name = '[u({unit_dbref}/UNITNAME.F,{unit_dbref})]'.format(
        unit_dbref=unit_dbref)
    mux_commands.name(p, unit_dbref, new_obj_name)
    mux_commands.trigger(p, unit_dbref, 'UPDATE_FREQ.T')
    if pilot_dbref:
        mux_commands.trigger(p, unit_dbref, 'SETLOADPREFS.T')

    # This tosses the unit on the map. At this point, they're 100% finished.
    yield think_fn_wrappers.btsetxy(
        p, unit_dbref, map_dbref, unit_x, unit_y, unit_z=unit_z)
    # Let any listening stuff know.
    on_unit_spawned.send(None, unit_dbref=unit_dbref, map_dbref=map_dbref)

    # Set default radio modes/comtitles.
    if pilot_dbref:
        pilot_alias = yield think_fn_wrappers.get(p, pilot_dbref, 'Alias')
        pilot_alias = pilot_alias.strip()
        if pilot_alias:
            comtitle = '%s/%s' % (unit_ref, pilot_alias)
        else:
            pilot_name = yield think_fn_wrappers.name(p, pilot_dbref)
            comtitle = '%s/%s' % (unit_ref, pilot_name)
        cmd = '@fo %s={setchanneltitle a=%s;setchannelmode a=deG}' % (
            unit_dbref, comtitle)
        mux_commands.force(p, unit_dbref, cmd)
        mux_commands.trigger(
            p, unit_dbref, 'SETLOADPREFS_TICS.T', [pilot_dbref, unit_ref])
    else:
        # No pilot specified, stay more generic.
        comtitle = unit_ref
        cmd = '@fo %s={setchanneltitle a=%s;setchannelmode a=deG}' % (
            unit_dbref, comtitle)
        mux_commands.force(p, unit_dbref, cmd)

    contact_id = yield think_fn_wrappers.btgetxcodevalue(
        p, unit_dbref, 'id')
    mechdesc = (
        '%ch%cb' + '-' * 78 + '%cn%r'
        '%[{contact_id}%] {unit_name} appears to be of type {unit_ref}.%r'
        '%ch%cb' + '-' * 78 + '%cn%r'
    ).format(
        contact_id=contact_id, unit_name=unit_name, unit_ref=unit_ref,
    )
    yield think_fn_wrappers.set_attrs(protocol, unit_dbref, {'Mechdesc': mechdesc})

    # The whole shebang completes with the deferred callback passing the
    # new unit's dbref.
    returnValue(unit_dbref)
