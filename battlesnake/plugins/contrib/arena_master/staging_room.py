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
        " %chCurrent state:%cn [ljust({game_state},30)]"
        " %chFriendlies remaining:%cn {remaining_friendlies}%r"
        " %chCurrent wave:%cn {current_wave}".format(
        game_state=arena_master_puppet.game_state,
        remaining_friendlies=len(remaining_friendlies),
        current_wave=arena_master_puppet.current_wave)
    )
    retval += get_footer_str('-')
    retval += ' To continue, type %ch%cgspawn <ref>'
    retval += get_footer_str()
    retval += "%r%r[u({staging_dbref}/EXITS_AND_CONTENTS.F)]".format(
        staging_dbref=staging_dbref)

    mux_commands.pemit(p, invoker_dbref, retval)
