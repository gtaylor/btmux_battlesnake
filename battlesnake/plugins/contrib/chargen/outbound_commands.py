from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def setup_new_player(protocol, player_dbref, archetype, sendto_dbref,
                     password=None):
    """
    Sets up a new player.

    :param BattlesnakeTelnetProtocol protocol:
    :param str player_dbref: The dbref of the player to set up.
    :param dict archetype: An archetype dict. See :py:mod:`chargen.archetypes`.
    :param str sendto_dbref: The dbref to send the player on to after successful
        setup.
    :keyword str password: If provided, set the given password.
    :rtype: defer.Deferred
    """

    p = protocol

    if password:
        yield mux_commands.newpassword(p, player_dbref, password)

    yield mux_commands.lock(p, player_dbref, player_dbref)
    yield mux_commands.lock(p, player_dbref, player_dbref, whichlock='use')
    yield mux_commands.lock(p, player_dbref, player_dbref, whichlock='enter')

    for attribute, val in archetype['physical_attributes'].items():
        yield think_fn_wrappers.btsetcharvalue(
            p, player_dbref, attribute, val, mode=0)
    for skill, val in archetype['skills'].items():
        yield think_fn_wrappers.btsetcharvalue(
            p, player_dbref, skill, val, mode=0)

    force_cmd = "@doing I'm new here!"
    yield mux_commands.force(p, player_dbref, force_cmd)
    yield think_fn_wrappers.teleport(protocol, player_dbref, sendto_dbref)
