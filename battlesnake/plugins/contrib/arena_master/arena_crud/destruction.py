from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.arena_master.db_api import \
    mark_match_as_destroyed_in_db
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE


@inlineCallbacks
def destroy_arena(protocol, arena_master_dbref):
    """
    Destroys all objects in an arena. If a match is running, abort it.
    All players are kicked back to default home.

    :param protocol:
    :param str arena_master_dbref: The dbref of the arena/zone master.
    """

    p = protocol
    puppet = yield PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
    yield mark_match_as_destroyed_in_db(puppet)
    _teleport_players_out(p, arena_master_dbref)
    yield _clear_map(p, arena_master_dbref)
    _destroy_zone_and_members(p, arena_master_dbref)
    yield PUPPET_STORE.remove_puppet_by_dbref(arena_master_dbref)


def _teleport_players_out(protocol, arena_master_dbref):
    """
    Get the players moved out immediately, rather than waiting for the @dbck.
    """

    default_home = settings['mux']['default_home_dbref']
    p = protocol
    dest_cmd = 'think [iter(zwho({arena_master_dbref}),tel(##,{default_home}))]'.format(
        arena_master_dbref=arena_master_dbref, default_home=default_home)
    p.write(dest_cmd)


@inlineCallbacks
def _clear_map(protocol, arena_master_dbref):
    """
    Due to some shit accounting within BTMux, we can't just go nuking mechs.
    There are some rare edge cases where crashes can happen. We have to send
    said mechs to the in-game garbage compacter, which gradually digests
    the XCODE objects.
    """

    p = protocol
    map_dbref = yield think_fn_wrappers.get(p, arena_master_dbref, 'MAP.DBREF')
    mux_commands.trigger(p, map_dbref, 'DEST_ALL_MECHS.T')
    mux_commands.force(p, map_dbref, 'CLEARMAP')


def _destroy_zone_and_members(protocol, arena_master_dbref):
    """
    Destroy all remaining non-mech objects.
    """

    p = protocol
    dest_cmd = '@dol [search(zone={arena_master_dbref})]={{@dest ##}}'.format(
        arena_master_dbref=arena_master_dbref)
    p.write(dest_cmd)
    mux_commands.destroy(p, arena_master_dbref)
    p.write('@wait 2=@dbck')
