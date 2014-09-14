"""
Emits and announcements.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def announce_arena_state_change(protocol, message):
    """
    Standard function for cemit'ing arena state changes. Only emits to
    those who are out of combat.
    """

    full_msg = '%ch%cgARENA:%cw {message}%cn'.format(message=message)

    # We do the setdiff() here to remove dupes.
    think_str = "[setdiff(iter(lwho(),ifelse(hasflag(loc(##),IN_CHARACTER),,##)),)]"
    func_result = yield mux_commands.think(protocol, think_str)
    ooc_players = func_result.split()
    mux_commands.pemit(protocol, ooc_players, full_msg)
