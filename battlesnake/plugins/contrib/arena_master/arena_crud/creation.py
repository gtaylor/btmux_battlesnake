from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import DEFENDER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


@inlineCallbacks
def create_arena(protocol, arena_name, creator_dbref):
    p = protocol
    arena_master_dbref = yield _create_arena_master_object(
        p, arena_name, creator_dbref)
    map_dbref = yield _create_map(p, arena_name, arena_master_dbref)
    puppet_ol_dbref = yield _create_puppet_ol(
        p, arena_name, arena_master_dbref, map_dbref)
    staging_dbref = yield _create_staging_room(
        p, arena_name, arena_master_dbref)

    arena_master_attrs = {
        'MAP.D': map_dbref,
        'PUPPET_OL.D': puppet_ol_dbref,
        'STAGING_ROOM.D': staging_dbref,
    }
    yield think_fn_wrappers.set_attrs(p, arena_master_dbref, arena_master_attrs)

    returnValue((arena_master_dbref, staging_dbref))


@inlineCallbacks
def _create_arena_master_object(protocol, arena_name, creator_dbref):
    p = protocol
    arena_master_name = "%ch%cyArenaPuppet:%cn " + arena_name
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


@inlineCallbacks
def _create_puppet_ol(protocol, arena_name, arena_master_dbref, map_dbref):
    p = protocol
    ol_name = "%ch%crArenaPuppetOL:%cn " + arena_name
    faction = get_faction(DEFENDER_FACTION_DBREF)
    extra_status_flags = ['COMBAT_SAFE', 'INVISIBLE', 'CLAIRVOYANT']
    ol_dbref = yield create_unit(p, 'RadioTower', map_dbref, faction,
                unit_x=0, unit_y=0,
                extra_status_flags=extra_status_flags,
                zone_dbref=arena_master_dbref)
    mux_commands.name(p, ol_dbref, ol_name)
    mux_commands.parent(
        p, ol_dbref,
        settings['arena_master']['puppet_ol_parent_dbref'])
    yield think_fn_wrappers.tel(p, arena_master_dbref, ol_dbref)

    returnValue(ol_dbref)


@inlineCallbacks
def _create_staging_room(protocol, arena_name, arena_master_dbref):
    p = protocol
    staging_name = "%ccStaging Room:%cn " + arena_name
    staging_dbref = yield think_fn_wrappers.create(p, staging_name, otype='r')
    mux_commands.chzone(p, staging_dbref, arena_master_dbref)
    mux_commands.parent(
        p, staging_dbref, settings['arena_master']['staging_room_parent_dbref'])

    flags = ['INHERIT']
    yield think_fn_wrappers.set_flags(p, staging_dbref, flags)

    returnValue(staging_dbref)
