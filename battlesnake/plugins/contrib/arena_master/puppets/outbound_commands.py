from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def order_ai(protocol, arena_puppet, orders):
    """
    Used to boss AI around through the puppet and its OL's radio.

    :param BattlesnakeTelnetProtocol protocol:
    :param ArenaMasterPuppet arena_puppet: The puppet to do the ordering.
    :param str orders: The orders to send to the AI.
    """

    command = "sendchannel a={orders}".format(orders=orders)
    yield mux_commands.force(
        protocol, arena_puppet.dbref,
        force_command=command)


@inlineCallbacks
def arena_debug_msg(protocol, message):
    """
    Emits an Arena debug message. Currently dumps to ArenaDebug channel
    in-game.

    :param str message: The message to emit.
    """

    yield think_fn_wrappers.cemit(protocol, 'ArenaDebug', message)
