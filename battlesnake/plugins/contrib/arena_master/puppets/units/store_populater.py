from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
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

    p = protocol
    print "Loading Arena Master puppets..."

    puppet_parent_dbref = settings['arena_master']['arena_master_parent_dbref']
    # Find all arena puppet master dbrefs.
    thought = "[children({parent_dbref})]".format(
        parent_dbref=puppet_parent_dbref)
    puppet_master_dbrefs = yield mux_commands.think(protocol, thought)
    # Returns a list of dbrefs which we can then call into the game for more
    # details on.
    puppet_master_split = puppet_master_dbrefs.split()
    for puppet_master_dbref in puppet_master_split:
        if not puppet_master_dbref:
            continue
        # This calls into the game to get enough details to instantiate an
        # ArenaMasterPuppet instace for our store.
        yield PUPPET_STORE.add_puppet_from_arena_master_object(
            p, puppet_master_dbref)
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
            "[btgetxcodevalue(##,critstatus2)]:"
            "[get(##/Faction)]:"
            "[btgetbv2_ref(get(##/Mechtype))]:"
            "[btgetxcodevalue(##,target)]:"
            "[btgetxcodevalue(##,shots_fired)]:"
            "[btgetxcodevalue(##,shots_hit)]:"
            "[btgetxcodevalue(##,damage_inflicted)]:"
            "[btgetxcodevalue(##,damage_taken)]:"
            "[btgetxcodevalue(##,shots_missed)]:"
            "[btgetxcodevalue(##,units_killed)]:"
            "[btgetxcodevalue(##,maxspeed)]:"
            "[default(##/IS_AI_CONTROLLED,0)]:"
            "[get(##/Pilot)]:"
            "[default(##/IS_POWERUP,0)]:"
            "[default(##/OPTIMAL_WEAP_RANGE.D,3)]:"
            "[btarmorstatus(##,all)]:"
            "[btgetxcodevalue(##,hexes_walked)]"
        "^)]"
    ).format(
        puppet_parent_dbref=puppet_parent_dbref, map_dbref=map_dbref
    )
    unit_data = yield mux_commands.think(protocol, thought)
    unit_data = unit_data.split('^')
    for unit_entry in unit_data:
        if not unit_entry:
            continue

        unit_split = unit_entry.split(':')
        dbref, contact_id, unit_ref, unit_type, unit_move_type, mech_name,\
            x_coord, y_coord, z_coord, speed, heading, tonnage, heat,\
            status, status2, critstatus, critstatus2, faction_dbref, \
            battle_value2, target_dbref, shots_fired, shots_landed,\
            damage_inflicted, damage_taken, shots_missed, units_killed, maxspeed,\
            is_ai, pilot_dbref, is_powerup, ai_optimal_weap_range,\
            armor_int_total, hexes_walked = unit_split
        unit_obj = ArenaMapUnit(
            dbref=dbref, contact_id=contact_id, unit_ref=unit_ref,
            unit_type=unit_type, unit_move_type=unit_move_type,
            mech_name=mech_name, x_coord=x_coord, y_coord=y_coord,
            z_coord=z_coord, speed=speed, heading=heading, tonnage=tonnage,
            heat=heat, status=status, status2=status2, critstatus=critstatus,
            critstatus2=critstatus2, faction_dbref=faction_dbref,
            battle_value2=battle_value2, target_dbref=target_dbref,
            shots_fired=shots_fired, shots_landed=shots_landed,
            damage_inflicted=damage_inflicted, damage_taken=damage_taken,
            shots_missed=shots_missed, units_killed=units_killed,
            maxspeed=maxspeed, is_ai=is_ai, pilot_dbref=pilot_dbref,
            is_powerup=is_powerup, ai_optimal_weap_range=ai_optimal_weap_range,
            armor_int_total=armor_int_total, hexes_walked=hexes_walked,
        )
        if not unit_obj.contact_id:
            continue
        if not unit_obj.mech_name:
            continue
        if unit_obj.is_invisible():
            continue

        arena_unit_store.update_or_add_unit(unit_obj)
    arena_unit_store.purge_stale_units()
