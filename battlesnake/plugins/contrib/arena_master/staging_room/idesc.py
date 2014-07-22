"""
Various components for the staging room.
"""

from battlesnake.core.utils import get_footer_str, get_header_str
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_STAGING, GAME_STATE_IN_BETWEEN, GAME_STATE_ACTIVE, \
    GAME_STATE_FINISHED, ARENA_DIFFICULTY_LEVELS


def pemit_staging_room_idesc(protocol, arena_master_puppet, invoker_dbref,
                             render_contents=True, render_header=False,
                             render_lower_tip=True):
    """
    @pemit the staging room's "idesc", showing a run-down of the arena's state.
    :param BattlesnakeTelnetProtocol protocol:
    :param ArenaMasterPuppet arena_master_puppet:
    :param str invoker_dbref:
    :keyword bool render_contents: Whether to render the contents of the
        staging room.
    """

    p = protocol

    defenders = arena_master_puppet.list_defending_units()
    attackers = arena_master_puppet.list_attacking_units()
    staging_dbref = arena_master_puppet.staging_dbref
    defender_bv2 = arena_master_puppet.calc_total_defending_units_bv2()
    attacker_bv2 = arena_master_puppet.calc_total_attacking_units_bv2()

    if render_header:
        header_txt = 'Arena {arena_id}'.format(
            arena_id=arena_master_puppet.id)
        retval = get_header_str(header_txt)
    else:
        retval = get_footer_str('-')

    retval += (
        "%r This arena is in %chwave%cn game mode. Survive increasingly more "
        "challenging waves%r of enemy AI attackers."
    )
    retval += get_footer_str('-')
    retval += (
        "%r [ljust(%chArena leader:%cn [name({arena_leader_dbref})],{lcol_ljust})]"
        " %chDifficulty%cn: {difficulty}%r"
        " [ljust(%chCurrent state:%cn {game_state},{lcol_ljust})]"
        " %chCurrent wave:%cn {current_wave}%r"
        " [ljust(%ch%ccDefenders remaining%cw:%cn {defenders} "
        "    %({defender_bv2} BV2%),{lcol_ljust})]"
        " %ch%cyAttackers remaining%cw:%cn {attackers} "
        "    %({attacker_bv2} BV2%)"
        "".format(
            lcol_ljust=40,
            arena_leader_dbref=arena_master_puppet.leader_dbref,
            difficulty=arena_master_puppet.difficulty_level.capitalize(),
            game_state=arena_master_puppet.game_state,
            current_wave=arena_master_puppet.current_wave,
            defenders=len(defenders),
            defender_bv2=defender_bv2,
            attackers=len(attackers),
            attacker_bv2=attacker_bv2)
    )
    if render_lower_tip:
        retval += get_footer_str('-')
        retval += '%r'
        retval += _return_state_specific_help(p, arena_master_puppet, invoker_dbref)
        if arena_master_puppet.leader_dbref == invoker_dbref:
            retval += "%r To transfer arena leadership to another player, type %ch%cgtransfer <player>%cn."
    retval += get_footer_str()
    if render_contents:
        retval += "%r%r[u({staging_dbref}/EXITS_AND_CONTENTS.F,{invoker_dbref})]".format(
            staging_dbref=staging_dbref, invoker_dbref=invoker_dbref)

    mux_commands.pemit(p, invoker_dbref, retval)


def _return_state_specific_help(protocol, arena_master_puppet, invoker_dbref):
    state = arena_master_puppet.game_state.lower()
    if state == GAME_STATE_STAGING:
        rfunc = _return_staging_state_help
    elif state == GAME_STATE_IN_BETWEEN:
        rfunc = _return_in_between_state_help
    elif state == GAME_STATE_ACTIVE:
        rfunc = _return_active_state_help
    elif state == GAME_STATE_FINISHED:
        rfunc = _return_finished_state_help
    else:
        raise ValueError("Invalid arena state: %s" % state)

    return rfunc(protocol, arena_master_puppet, invoker_dbref)


# noinspection PyUnusedLocal
def _return_staging_state_help(protocol, arena_master_puppet, invoker_dbref):
    leader_dbref = arena_master_puppet.leader_dbref
    if leader_dbref == invoker_dbref:
        difficulty_vals = '|'.join(ARENA_DIFFICULTY_LEVELS)
        retval = (
            ' To set the difficulty level, type %ch%cgdifficulty <{difficulty_vals}>%cn.%r'
            ' Once you are ready to get the match started, type %ch%cgbegin%cn.%r'
            ' To cancel the match and delete the arena, type %ch%cgend%cn.'.format(
                difficulty_vals=difficulty_vals))
    else:
        retval = ' The match will begin once [name(%s)] presses the big red button.' % leader_dbref
    return retval


# noinspection PyUnusedLocal
def _return_in_between_state_help(protocol, arena_master_puppet, invoker_dbref):
    retval = (
        " The arena is currently in between waves. If you'd like to join %r"
        " the action, now is your chance!%r%r"
        " Type %ch%cgspawn <ref>%cn to spawn a unit of your choice"
    )
    leader_dbref = arena_master_puppet.leader_dbref
    if leader_dbref == invoker_dbref:
        retval += "%r To end the match, type %ch%cgend%cn."
    return retval


# noinspection PyUnusedLocal
def _return_active_state_help(protocol, arena_master_puppet, invoker_dbref):
    retval = (
        " Your fellow humans are currently fending off a wave of homicidal AI foes.%r"
        " You'll be able to join the action once the wave is finished."
    )
    return retval


# noinspection PyUnusedLocal
def _return_finished_state_help(protocol, arena_master_puppet, invoker_dbref):
    leader_dbref = arena_master_puppet.leader_dbref
    if leader_dbref == invoker_dbref:
        retval = (
            " %ch%cyAll defenders have perished, the match has finished.%cn"
            "%r Type %ch%cgend%cn to close the arena, or "
            "%ch%cgrestart%cn to start back at wave 1."
        )
    else:
        retval = "%r The match has concluded. Hit the showers!"
    return retval
