"""
Channel emits and external hooks.
"""

from battlesnake.outbound_commands import mux_commands

# This may change as we get more activity.
ARENA_CHANNEL = "Public"


def cemit_arena_state_change(protocol, message):
    """
    Standard function for cemit'ing arena state changes.
    """

    full_msg = '%ch%cgARENA:%cw {message}%cn'.format(message=message)
    mux_commands.cemit(
        protocol, ARENA_CHANNEL, full_msg, no_header=True, force_cemit=True)
