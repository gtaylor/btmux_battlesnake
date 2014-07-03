from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands

from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import DEFENDER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_library.api import get_unit_by_ref
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit

from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.staging_room.idesc import \
    pemit_staging_room_idesc


class ArenaInternalDescriptionCommand(BaseCommand):
    """
    This gets emitted immediately following the staging room's name line,
    giving it the appearance of being the room's description. It contains
    a summary of the status of the arena.
    """

    command_name = "am_arenaidesc"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol

        arena_master_dbref = parsed_line.kwargs['arena_dbref']
        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError(
                "Invalid arena ID. Please notify a staff member.")

        pemit_staging_room_idesc(p, puppet, invoker_dbref)


class SimpleSpawnCommand(BaseCommand):
    """
    A really basic spawn command we can use to test arenas.
    """

    command_name = "am_simplespawn"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        unit_ref = parsed_line.kwargs['unit_ref']
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        unit = yield get_unit_by_ref(unit_ref)
        if not unit:
            raise CommandError('Invalid unit reference!')

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        yield think_fn_wrappers.btsetcharvalue(p, invoker_dbref, 'bruise', 0, 0)
        yield think_fn_wrappers.btsetcharvalue(p, invoker_dbref, 'lethal', 0, 0)

        map_dbref = puppet.map_dbref
        faction = get_faction(DEFENDER_FACTION_DBREF)
        unit_x, unit_y = puppet.get_defender_spawn_coords()

        unit_dbref = yield create_unit(
            p, unit.reference, map_dbref, faction, unit_x, unit_y,
            pilot_dbref=invoker_dbref, zone_dbref=arena_master_dbref)
        yield think_fn_wrappers.tel(p, invoker_dbref, unit_dbref)
        yield mux_commands.force(p, invoker_dbref, 'startup')


class BeginMatchCommand(BaseCommand):
    """
    Gets the party started. Allows spawning, sets to "In-Between" state,
    and is one command away from releasing the kraken.
    """

    command_name = "am_beginmatch"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        creator_dbref = puppet.creator_dbref
        if creator_dbref != invoker_dbref:
            raise CommandError("Only the arena's original creator can do that.")

        if puppet.game_state.lower() != 'staging':
            raise CommandError("The match has already begun!")

        yield puppet.change_game_state(p, 'In-Between')
        puppet.pemit_throughout_zone(p, "The match has begun. You may now spawn.")


class ArenaStagingRoomCommandTable(InboundCommandTable):

    commands = [
        ArenaInternalDescriptionCommand,
        BeginMatchCommand,
        SimpleSpawnCommand,
    ]
