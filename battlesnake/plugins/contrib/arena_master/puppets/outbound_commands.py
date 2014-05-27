from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def populate_puppet_store(protocol):
    """
    :rtype: defer.Deferred
    :returns: A Deferred whose callback value will be a list of ArenaMasterPuppet
        instances.
    """

    p = protocol

    parent_dbref = settings['arena_master']['arena_master_parent_dbref']

    thought = "[iter(children({parent_dbref}), ##:[rloc(##,2)]|)]".format(
        parent_dbref=parent_dbref,
    )
    puppet_data = yield mux_commands.think(p, thought)
    print "PUPPET DATA", puppet_data

    returnValue(puppet_data)
