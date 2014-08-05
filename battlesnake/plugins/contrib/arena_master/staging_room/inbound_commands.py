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

from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_STAGING, GAME_STATE_FINISHED, GAME_STATE_IN_BETWEEN, \
    ARENA_DIFFICULTY_LEVELS, GAME_STATE_ACTIVE
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.staging_room.idesc import \
    pemit_staging_room_idesc
from battlesnake.plugins.contrib.arena_master.arena_crud.destruction import \
    destroy_arena


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

        try:
            unit = yield get_unit_by_ref(unit_ref)
        except ValueError:
            raise CommandError('Invalid unit reference!')

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        game_state = puppet.game_state
        if game_state == GAME_STATE_STAGING:
            raise CommandError(
                "The match hasn't started yet. The arena leader still needs "
                "to %ch%cgbegin%cn.")
        elif game_state == GAME_STATE_FINISHED:
            raise CommandError("The match is already over!")
        elif game_state != GAME_STATE_IN_BETWEEN:
            raise CommandError("You can only spawn between waves.")

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
        message = (
            "[name({invoker_dbref})] has spawned a "
            "%ch[ucstr({unit_ref})]%cn.".format(
                invoker_dbref=invoker_dbref, unit_ref=unit_ref)
        )
        puppet.pemit_throughout_zone(p, message)


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

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        game_state = puppet.game_state
        if game_state == GAME_STATE_FINISHED:
            raise CommandError("The match is already over!")
        elif game_state != GAME_STATE_STAGING:
            raise CommandError("The match has already begun!")

        yield puppet.change_game_state(p, GAME_STATE_IN_BETWEEN)
        puppet.pemit_throughout_zone(
            p, "The match has begun. You may now %ch%cgspawn%cn.")


class EndMatchCommand(BaseCommand):
    """
    Lets the arena leader end the match and clean the arena up.
    """

    command_name = "am_endmatch"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        game_state = puppet.game_state
        if game_state == GAME_STATE_ACTIVE:
            raise CommandError("You can't end a match while a wave is underway.")

        if game_state != GAME_STATE_FINISHED:
            yield puppet.change_game_state(p, GAME_STATE_FINISHED)
        puppet.pemit_throughout_zone(
            p, "[name({invoker_dbref})] has ended the match.".format(
                invoker_dbref=invoker_dbref))
        yield destroy_arena(p, arena_master_dbref)
        

class RestartMatchCommand(BaseCommand):
    """
    Lets the arena leader reset the arena to wave 1 and go again.
    """

    command_name = "am_restartmatch"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        game_state = puppet.game_state
        if game_state != GAME_STATE_FINISHED:
            raise CommandError("You can only restart a finished match.")

        yield puppet.reset_arena(p)


class TransferLeaderStatusCommand(BaseCommand):
    """
    Transfers the arena leader status to someone else.
    """

    command_name = "am_transferleader"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        new_leader_dbref = parsed_line.kwargs['new_leader_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        message = (
            "%ch%cy[name({invoker_dbref})]%cw has transferred arena leadership "
            "to %cc[name({new_leader_dbref})]%cw.%cn".format(
                invoker_dbref=invoker_dbref, new_leader_dbref=new_leader_dbref))
        puppet.pemit_throughout_zone(p, message)
        yield puppet.set_arena_leader(p, new_leader_dbref)


class SetDifficultyCommand(BaseCommand):
    """
    Used to adjust an arena's difficulty modifier.
    """

    command_name = "am_setdifficulty"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        difficulty_level = parsed_line.kwargs['difficulty_level']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        game_state = puppet.game_state
        if game_state != GAME_STATE_STAGING:
            raise CommandError(
                "Difficulty can only be adjusted during pre-match staging.")

        difficulty_level = difficulty_level.lower()
        if difficulty_level not in ARENA_DIFFICULTY_LEVELS:
            raise CommandError(
                "Invalid difficulty level. Must be one of: %s" % (
                    ', '.join(ARENA_DIFFICULTY_LEVELS),)
            )

        yield puppet.set_difficulty(p, difficulty_level)


class ArenaStagingRoomCommandTable(InboundCommandTable):

    commands = [
        ArenaInternalDescriptionCommand,
        SetDifficultyCommand,
        BeginMatchCommand,
        SimpleSpawnCommand,
        EndMatchCommand,
        RestartMatchCommand,
        TransferLeaderStatusCommand,
    ]
