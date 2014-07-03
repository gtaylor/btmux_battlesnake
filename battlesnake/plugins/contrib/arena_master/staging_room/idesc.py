"""
Various components for the staging room.
"""

from battlesnake.core.utils import get_footer_str
from battlesnake.outbound_commands import mux_commands


def pemit_staging_room_idesc(protocol, arena_master_puppet, invoker_dbref):
    """
    @pemit the staging room's "idesc", showing a run-down of the arena's state.
    :param BattlesnakeTelnetProtocol protocol:
    :param ArenaMasterPuppet arena_master_puppet:
    :param str invoker_dbref:
    """

    p = protocol

    remaining_friendlies = arena_master_puppet.list_defending_units()
    staging_dbref = arena_master_puppet.staging_dbref

    retval = get_footer_str('-')
    retval += (
        " This arena is in %chwave%cn game mode. Survive increasingly more "
        "challenging waves of enemy AI."
    )
    retval += get_footer_str('-')
    retval += (
        " [ljust(%chMap name:%cn [btgetxcodevalue({map_dbref},mapname)],45)]"
        " %chGame mode%cn: {game_mode}%r"
        " [ljust(%chCurrent state:%cn {game_state},45)]"
        " %chFriendlies remaining:%cn {remaining_friendlies}%r"
        " %chCurrent wave:%cn {current_wave}".format(
            map_dbref=arena_master_puppet.map_dbref,
            game_mode='Wave',
            game_state=arena_master_puppet.game_state,
            remaining_friendlies=len(remaining_friendlies),
            current_wave=arena_master_puppet.current_wave)
    )
    retval += get_footer_str('-')
    retval += _return_state_specific_help(p, arena_master_puppet, invoker_dbref)
    retval += get_footer_str()
    retval += "%r%r[u({staging_dbref}/EXITS_AND_CONTENTS.F)]".format(
        staging_dbref=staging_dbref)

    mux_commands.pemit(p, invoker_dbref, retval)


def _return_state_specific_help(protocol, arena_master_puppet, invoker_dbref):
    state = arena_master_puppet.game_state.lower()
    if state == 'staging':
        rfunc = _return_staging_state_help
    elif state == 'in-between':
        rfunc = _return_in_between_state_help
    elif state == 'active':
        rfunc = _return_active_state_help
    elif state == 'finished':
        rfunc = _return_finished_state_help
    else:
        raise ValueError("Invalid arena state: %s" % state)

    return rfunc(protocol, arena_master_puppet, invoker_dbref)


# noinspection PyUnusedLocal
def _return_staging_state_help(protocol, arena_master_puppet, invoker_dbref):
    creator_dbref = arena_master_puppet.creator_dbref
    if creator_dbref == invoker_dbref:
        retval = ' Once you are ready to get the match started, type %ch%cgbegin%cn.'
    else:
        retval = ' The match will begin once [name(%s)] presses the big red button.' % creator_dbref
    return retval


# noinspection PyUnusedLocal
def _return_in_between_state_help(protocol, arena_master_puppet, invoker_dbref):
    retval = (
        " The arena is currently in between waves. If you'd like to join "
        "the action, now is your chance!%r%r"
        " Type %ch%cgspawn <ref>%cn to spawn a unit of your choice"
    )
    return retval


# noinspection PyUnusedLocal
def _return_active_state_help(protocol, arena_master_puppet, invoker_dbref):
    retval = (
        " Your fellow humans are currently fending off a wave of homicidal "
        " AI foes. You'll be able to join the action once the wave is finished."
    )
    return retval


# noinspection PyUnusedLocal
def _return_finished_state_help(protocol, arena_master_puppet, invoker_dbref):
    retval = (
        " The match has concluded. Hit the showers!"
    )
    return retval
