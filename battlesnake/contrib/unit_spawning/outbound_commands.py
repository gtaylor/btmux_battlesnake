from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.contrib.unit_spawning.signals import on_unit_spawned
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
    unit_dbref = yield think_fn_wrappers.create(protocol, unit_name, otype='t')

    # I can't remember the details, but there were some edge cases where not
    # having a negative semaphore count caused issues.
    yield mux_commands.drain(p, unit_dbref)
    yield mux_commands.notify(p, unit_dbref)
    yield mux_commands.parent(p, unit_dbref, settings['unit_spawning']['unit_parent_dbref'])
    yield mux_commands.lock(p, unit_dbref, unit_dbref)
    yield mux_commands.lock(p, unit_dbref, 'ELOCK/1', whichlock='enter')
    yield mux_commands.lock(p, unit_dbref, 'LLOCK/1', whichlock='leave')
    yield mux_commands.lock(p, unit_dbref, 'ULOCK/1', whichlock='use')
    yield mux_commands.link(protocol, unit_dbref, map_dbref)
    unit_attrs = {
        'Mechtype': unit_ref,
        'Mechname': 'Loading...',
        'FACTION': faction.dbref,
        'Xtype': 'MECH',
    }
    if pilot_dbref:
        unit_attrs['Pilot'] = pilot_dbref
    yield think_fn_wrappers.set_attrs(protocol, unit_dbref, unit_attrs)

    yield think_fn_wrappers.teleport(protocol, unit_dbref, map_dbref)
    flags = ['INHERIT', 'IN_CHARACTER', 'XCODE', 'ENTER_OK', 'OPAQUE']
    # At this point, the XCODE flag is set, so we're ready to rock.
    yield think_fn_wrappers.set_flags(protocol, unit_dbref, flags)

    # The unit now has its ref loaded, but is still not on a map.
    yield think_fn_wrappers.btloadmech(p, unit_dbref, unit_ref)
    yield think_fn_wrappers.btsetxcodevalue(p, unit_dbref, 'team', faction.team_num)
    # Get the name of the ref from the unit's mechname XCODE value.
    unit_name = yield think_fn_wrappers.btgetxcodevalue(p, unit_dbref, 'mechname')
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
    # The whole shebang completes with the deferred callback passing the
    # new unit's dbref.
    returnValue(unit_dbref)
