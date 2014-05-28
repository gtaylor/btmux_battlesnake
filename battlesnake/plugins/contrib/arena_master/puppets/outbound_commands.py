from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    ArenaMasterPuppet, PUPPET_STORE


@inlineCallbacks
def populate_puppet_store(protocol):
    """
    Called at startup to figure out what arena puppets have already been
    created and are in active use.

    :rtype: defer.Deferred
    :returns: A Deferred whose callback value will be a list of ArenaMasterPuppet
        instances.
    """

    p = protocol
    print "Loading Arena Master puppets"

    parent_dbref = settings['arena_master']['arena_master_parent_dbref']
    # puppet_dbref, map_dbref
    thought = "[iter(children({parent_dbref}), ##:[rloc(##,2)]|)]".format(
        parent_dbref=parent_dbref,
    )
    puppet_data = yield mux_commands.think(p, thought)
    puppet_data = puppet_data.split('|')
    for puppet_entry in puppet_data:
        if not puppet_entry:
            continue
        puppet_split = puppet_entry.split(':')
        puppet_dbref, map_dbref = puppet_split
        puppet_obj = ArenaMasterPuppet(puppet_dbref, map_dbref)
        PUPPET_STORE.update_or_add_puppet(puppet_obj)
    print "  - ", PUPPET_STORE.puppet_count, "puppets loaded"
