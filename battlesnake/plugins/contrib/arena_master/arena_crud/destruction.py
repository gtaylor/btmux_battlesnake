from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def destroy_arena(protocol, arena_master_dbref):
    p = protocol
    yield _clear_map(p, arena_master_dbref)
    _destroy_zone_and_members(protocol, arena_master_dbref)


@inlineCallbacks
def _clear_map(protocol, arena_master_dbref):
    p = protocol
    map_dbref = yield think_fn_wrappers.get(protocol, arena_master_dbref, 'MAP.D')
    mux_commands.trigger(p, map_dbref, 'DEST_ALL_MECHS.T')
    mux_commands.force(p, map_dbref, 'CLEARMAP')


def _destroy_zone_and_members(protocol, arena_master_dbref):
    p = protocol
    dest_cmd = '@dol [search(zone={arena_master_dbref})]={{@dest ##}}'.format(
        arena_master_dbref=arena_master_dbref)
    protocol.write(dest_cmd)
    mux_commands.destroy(p, arena_master_dbref)
    protocol.write('@wait 2=@dbck')
