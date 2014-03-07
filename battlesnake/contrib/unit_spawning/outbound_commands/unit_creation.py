from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def create_unit(protocol, unit_ref, map_dbref, faction_name, unit_x, unit_y):
    unit_name = "UnitBeingCreated"
    unit_parent_dbref = settings['unit_spawning']['unit_parent_dbref']
    unit_dbref = yield think_fn_wrappers.create(protocol, unit_name, otype='t')
    yield think_fn_wrappers.set_attrs(protocol, unit_dbref, {
        'Mechtype': unit_ref,
        'Mechname': 'Fun unit',
        'FACTION': faction_name,
        'Xtype': 'MECH',

    })
    yield think_fn_wrappers.teleport(protocol, unit_dbref, map_dbref)
    flags = ['INHERIT', 'IN_CHARACTER', 'XCODE', 'ENTER_OK', 'OPAQUE']
    yield think_fn_wrappers.set_flags(protocol, unit_dbref, flags)
    mux_commands.parent(protocol, unit_dbref, unit_parent_dbref)
    yield think_fn_wrappers.btloadmech(protocol, unit_dbref, unit_ref)
    yield think_fn_wrappers.btsetxy(
        protocol, unit_dbref, map_dbref, unit_x, unit_y)
    returnValue(unit_dbref)
