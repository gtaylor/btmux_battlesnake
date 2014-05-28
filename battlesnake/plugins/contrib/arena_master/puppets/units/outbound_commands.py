from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    ArenaMasterPuppet, PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnit


@inlineCallbacks
def populate_puppet_store(protocol):
    """
    Called at startup to figure out what arena puppets have already been
    created and are in active use.

    :param BattlesnakeTelnetProtocol protocol:
    :rtype: defer.Deferred
    :returns: A Deferred whose callback value will be a list of ArenaMasterPuppet
        instances.
    """

    print "Loading Arena Master puppets..."

    puppet_parent_dbref = settings['arena_master']['arena_master_parent_dbref']
    # puppet_dbref, map_dbref
    thought = "[iter(children({parent_dbref}), ##:[rloc(##,2)]|)]".format(
        parent_dbref=puppet_parent_dbref,
    )
    puppet_data = yield mux_commands.think(protocol, thought)
    puppet_data = puppet_data.split('|')
    for puppet_entry in puppet_data:
        if not puppet_entry:
            continue
        puppet_split = puppet_entry.split(':')
        puppet_dbref, map_dbref = puppet_split
        puppet_obj = ArenaMasterPuppet(puppet_dbref, map_dbref)
        PUPPET_STORE.update_or_add_puppet(puppet_obj)
    print "  - ", PUPPET_STORE.puppet_count, "puppets loaded"


@inlineCallbacks
def update_store_from_btfuncs(protocol, arena_unit_store):
    """
    Given an arena's unit store, update the cached mechs by iterating over all
    mechs on the arena's map and pulling xcode and attrib values. This is a
    spammy, inefficient way to go about getting this data, but this is a
    proof of concept.

    :param BattlesnakeTelnetProtocol protocol:
    :param ArenaMapUnitStore arena_unit_store: The unit store to update.
    """

    puppet_parent_dbref = settings['arena_master']['arena_master_parent_dbref']
    map_dbref = arena_unit_store.arena_master_puppet.map_dbref
    thought = (
        "[setq(0,filter({puppet_parent_dbref}/IS_SCENARIO_UNIT.F, lcon({map_dbref})))]"
        "[iter(%q0,"
            "##:"
            "[btgetxcodevalue(##,id)]:"
            "[get(##/Mechtype)]:"
            "[btgetxcodevalue(##,mechtype)]:"
            "[btgetxcodevalue(##,mechmovetype)]:"
            "[get(##/Mechname)]:"
            "[btgetxcodevalue(##,x)]:"
            "[btgetxcodevalue(##,y)]:"
            "[btgetxcodevalue(##,z)]:"
            "[btgetxcodevalue(##,speed)]:"
            "[btgetxcodevalue(##,heading)]:"
            "[btgetxcodevalue(##,tons)]:"
            "[btgetxcodevalue(##,heat)]:"
            "[btgetxcodevalue(##,status)]:"
            "[btgetxcodevalue(##,status2)]:"
            "[btgetxcodevalue(##,critstatus)]:"
            "[get(##/Faction)]:"
            "[btgetxcodevalue(##,bv)]"
        "|)]"
    ).format(
        puppet_parent_dbref=puppet_parent_dbref, map_dbref=map_dbref
    )
    unit_data = yield mux_commands.think(protocol, thought)
    unit_data = unit_data.split('|')
    for unit_entry in unit_data:
        if not unit_entry:
            continue
        unit_split = unit_entry.split(':')
        dbref, contact_id, unit_ref, unit_type, unit_move_type, mech_name,\
            x_coord, y_coord, z_coord, speed, heading, tonnage, heat,\
            status, status2, critstatus, faction_dbref, battle_value = unit_split
        unit_obj = ArenaMapUnit(
            dbref=dbref, contact_id=contact_id, unit_ref=unit_ref,
            unit_type=unit_type, unit_move_type=unit_move_type,
            mech_name=mech_name, x_coord=x_coord, y_coord=y_coord,
            z_coord=z_coord, speed=speed, heading=heading, tonnage=tonnage,
            heat=heat, status=status, status2=status2, critstatus=critstatus,
            faction_dbref=faction_dbref, battle_value=battle_value,
        )
        arena_unit_store.update_or_add_unit(unit_obj)
    arena_unit_store.purge_stale_units()
