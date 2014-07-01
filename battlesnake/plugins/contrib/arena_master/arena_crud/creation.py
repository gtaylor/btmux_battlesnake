from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def create_arena(protocol, arena_name, creator_dbref):
    p = protocol
    arena_master_dbref = yield _create_arena_master_object(
        p, arena_name, creator_dbref)
    map_dbref = yield _create_map(p, arena_name, arena_master_dbref)

    arena_master_attrs = {
        'MAP.D': map_dbref,
    }
    yield think_fn_wrappers.set_attrs(p, arena_master_dbref, arena_master_attrs)


@inlineCallbacks
def _create_arena_master_object(protocol, arena_name, creator_dbref):
    p = protocol
    arena_master_name = "%ch%cyArenaMaster:%cn " + arena_name
    arena_master_dbref = yield think_fn_wrappers.create(
        p, arena_master_name, otype='t')

    mux_commands.parent(
        p, arena_master_dbref,
        settings['arena_master']['arena_master_parent_dbref'])

    flags = ['INHERIT']
    yield think_fn_wrappers.set_flags(protocol, arena_master_dbref, flags)

    attrs = {
        'CREATED_BY.D': creator_dbref,
    }
    yield think_fn_wrappers.set_attrs(protocol, arena_master_dbref, attrs)
    returnValue(arena_master_dbref)


@inlineCallbacks
def _create_map(protocol, arena_name, arena_master_dbref):
    p = protocol
    map_name = "%ch%cgArenaMap:%cn " + arena_name
    map_dbref = yield think_fn_wrappers.create(p, map_name, otype='t')
    mux_commands.chzone(p, map_dbref, arena_master_dbref)
    mux_commands.parent(
        p, map_dbref, settings['arena_master']['map_parent_dbref'])

    map_attrs = {
        'Xtype': 'MAP',
    }
    yield think_fn_wrappers.set_attrs(p, map_dbref, map_attrs)

    flags = ['INHERIT', 'IN_CHARACTER', 'XCODE']
    yield think_fn_wrappers.set_flags(p, map_dbref, flags)

    returnValue(map_dbref)
