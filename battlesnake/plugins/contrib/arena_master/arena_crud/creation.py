from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import DEFENDER_FACTION_DBREF, \
    ATTACKER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


@inlineCallbacks
def create_arena(protocol, arena_name, creator_dbref):
    p = protocol
    arena_master_dbref = yield _create_arena_master_object(p, arena_name)
    map_dbref = yield _create_map(p, arena_name, arena_master_dbref)
    puppet_ol_dbref = yield _create_puppet_ol(
        p, arena_name, arena_master_dbref, map_dbref)
    staging_dbref = yield _create_staging_room(
        p, arena_name, arena_master_dbref, map_dbref, creator_dbref)

    arena_master_attrs = {
        'ARENA_NAME.D': arena_name,
        'MAP.D': map_dbref,
        'CREATOR.D': creator_dbref,
        'PUPPET_OL.D': puppet_ol_dbref,
        'STAGING_ROOM.D': staging_dbref,

        'CURRENT_WAVE.D': '1',
        'GAME_MODE.D': 'wave',
        'GAME_STATE.D': 'Staging',
    }
    yield think_fn_wrappers.set_attrs(p, arena_master_dbref, arena_master_attrs)
    yield PUPPET_STORE.add_puppet_from_arena_master_object(p, arena_master_dbref)

    returnValue((arena_master_dbref, staging_dbref))


@inlineCallbacks
def _create_arena_master_object(protocol, arena_name):
    p = protocol
    arena_master_name = "%cyArenaPuppet:%cn " + arena_name
    arena_master_dbref = yield think_fn_wrappers.create(
        p, arena_master_name, otype='t')

    mux_commands.parent(
        p, arena_master_dbref,
        settings['arena_master']['arena_master_parent_dbref'])

    flags = ['INHERIT']
    yield think_fn_wrappers.set_flags(protocol, arena_master_dbref, flags)

    returnValue(arena_master_dbref)


@inlineCallbacks
def _create_map(protocol, arena_name, arena_master_dbref):
    p = protocol
    map_name = "%ch%cgArenaMap:%cn " + arena_name
    map_dbref = yield think_fn_wrappers.create(p, map_name, otype='t')
    mux_commands.chzone(p, map_dbref, arena_master_dbref)
    mux_commands.parent(
        p, map_dbref, settings['arena_master']['map_parent_dbref'])
    mux_commands.lock(p, map_dbref, 'ELOCK/1', whichlock='enter')

    yield think_fn_wrappers.set_attrs(p, map_dbref, {'Xtype': 'MAP'})
    flags = ['INHERIT', 'IN_CHARACTER', 'XCODE']
    yield think_fn_wrappers.set_flags(p, map_dbref, flags)

    returnValue(map_dbref)


@inlineCallbacks
def _create_puppet_ol(protocol, arena_name, arena_master_dbref, map_dbref):
    p = protocol
    ol_name = "%ch%crArenaPuppetOL:%cn " + arena_name
    faction = get_faction(ATTACKER_FACTION_DBREF)
    extra_status_flags = ['COMBAT_SAFE', 'INVISIBLE', 'CLAIRVOYANT']
    ol_dbref = yield create_unit(
        p, 'RadioTower', map_dbref, faction, unit_x=0, unit_y=0,
        extra_status_flags=extra_status_flags, zone_dbref=arena_master_dbref)
    mux_commands.name(p, ol_dbref, ol_name)
    mux_commands.parent(
        p, ol_dbref, settings['arena_master']['puppet_ol_parent_dbref'])
    yield think_fn_wrappers.tel(p, arena_master_dbref, ol_dbref)

    returnValue(ol_dbref)


@inlineCallbacks
def _create_staging_room(protocol, arena_name, arena_master_dbref, map_dbref,
                         creator_dbref):
    p = protocol
    staging_name = "%ccStaging Room:%cn " + arena_name
    faction = get_faction(DEFENDER_FACTION_DBREF)
    extra_status_flags = ['COMBAT_SAFE', 'INVISIBLE', 'CLAIRVOYANT']
    staging_dbref = yield create_unit(
        p, 'RadioTower', map_dbref, faction, unit_x=0, unit_y=0,
        extra_status_flags=extra_status_flags, zone_dbref=arena_master_dbref)
    mux_commands.name(p, staging_dbref, staging_name)
    mux_commands.parent(
        p, staging_dbref, settings['arena_master']['staging_room_parent_dbref'])
    yield think_fn_wrappers.tel(p, staging_dbref, map_dbref)
    yield think_fn_wrappers.set_flags(p, staging_dbref, ['DARK'])

    exit_dbref = yield think_fn_wrappers.create(p, 'Out to Nexus;o', otype='e')
    yield think_fn_wrappers.tel(p, exit_dbref, staging_dbref)
    nexus_dbref = settings['arena_master']['nexus_dbref']
    mux_commands.chzone(p, exit_dbref, arena_master_dbref)
    mux_commands.link(p, exit_dbref, nexus_dbref)
    mux_commands.set_attr(
        p, exit_dbref, 'ISOWNER', '[strmatch(%#,get(zone(me)/CREATOR.D))]')
    # Make sure the owner can't leave.
    mux_commands.lock(p, exit_dbref, 'ISOWNER/0')
    mux_commands.set_attr(
        p, exit_dbref, 'Fail',
        "You can't leave your own arena without destroying it.")

    returnValue(staging_dbref)