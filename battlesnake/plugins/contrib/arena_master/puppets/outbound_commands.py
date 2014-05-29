from twisted.internet.defer import inlineCallbacks

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
