from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions
from battlesnake.plugins.contrib.ai.outbound_commands import start_unit_ai

from battlesnake.plugins.contrib.arena_master.puppets.puppet import \
    ArenaMasterPuppet
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnit
from battlesnake.plugins.contrib.arena_master.puppets.units.waves import \
    pick_refs_for_wave, choose_unit_spawn_spot
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


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
    thought = (
        "[iter(children({parent_dbref}), "
            # puppet_dbref
            "##:"
            # map_dbref
            "[setr(0,rloc(##,2))]:"
            "[btgetxcodevalue(%q0,mapwidth)] [btgetxcodevalue(%q0,mapheight)]"
        "|)]".format(parent_dbref=puppet_parent_dbref)
    )
    puppet_data = yield mux_commands.think(protocol, thought)
    puppet_data = puppet_data.split('|')
    for puppet_entry in puppet_data:
        if not puppet_entry:
            continue
        puppet_split = puppet_entry.split(':')
        puppet_dbref, map_dbref, map_dimensions = puppet_split
        map_height, map_width = map_dimensions.split()
        puppet_obj = ArenaMasterPuppet(
            protocol, puppet_dbref, map_dbref, map_height, map_width)
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
            "[btgetxcodevalue(##,critstatus2)]:"
            "[get(##/Faction)]:"
            "[btgetxcodevalue(##,bv)]:"
            "[btgetxcodevalue(##,target)]:"
            "[btgetxcodevalue(##,shots_fired)]:"
            "[btgetxcodevalue(##,shots_hit)]:"
            "[btgetxcodevalue(##,damage_inflicted)]:"
            "[btgetxcodevalue(##,shots_missed)]:"
            "[btgetxcodevalue(##,units_killed)]:"
            "[btgetxcodevalue(##,maxspeed)]:"
            "[default(##/IS_AI_CONTROLLED,0)]"
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
            status, status2, critstatus, critstatus2, faction_dbref, \
            battle_value, target_dbref, shots_fired, shots_landed,\
            damage_inflicted, shots_missed, units_killed, maxspeed,\
            is_ai = unit_split
        unit_obj = ArenaMapUnit(
            dbref=dbref, contact_id=contact_id, unit_ref=unit_ref,
            unit_type=unit_type, unit_move_type=unit_move_type,
            mech_name=mech_name, x_coord=x_coord, y_coord=y_coord,
            z_coord=z_coord, speed=speed, heading=heading, tonnage=tonnage,
            heat=heat, status=status, status2=status2, critstatus=critstatus,
            critstatus2=critstatus2, faction_dbref=faction_dbref,
            battle_value=battle_value, target_dbref=target_dbref,
            shots_fired=shots_fired, shots_landed=shots_landed,
            damage_inflicted=damage_inflicted, shots_missed=shots_missed,
            units_killed=units_killed, maxspeed=maxspeed, is_ai=is_ai,
        )
        if not unit_obj.contact_id:
            continue
        if not unit_obj.mech_name:
            continue
        if unit_obj.is_invisible():
            continue

        arena_unit_store.update_or_add_unit(unit_obj)
    arena_unit_store.purge_stale_units()


@inlineCallbacks
def spawn_wave(protocol, wave_num, num_players, difficulty_modifier,
               map_dbref):
    """
    Spawns a wave of attackers.

    :param BattlesnakeTelnetProtocol protocol:
    :param int wave_num: The wave number to spawn. Higher waves are
        more difficult.
    :param int num_players: The number of defending players.
    :param float difficulty_modifier: 1.0 = moderate difficulty,
        anything less is easier, anything more is harder.
    :param str map_dbref: The DBref of the map to spawn units to.
    :rtype: list
    :returns: A list of tuples containing details on the spawned units.
        Tuples are in the form of (unit_ref, unit_dbref).
    """

    map_width, map_height = yield get_map_dimensions(protocol, map_dbref)
    refs = yield pick_refs_for_wave(wave_num, num_players, difficulty_modifier)
    faction = get_faction(ATTACKER_FACTION_DBREF)
    spawned = []
    for unit_ref in refs:
        unit_x, unit_y = choose_unit_spawn_spot(map_width, map_height)
        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction, unit_x, unit_y)
        start_unit_ai(protocol, unit_dbref)
        spawned.append((unit_ref, unit_dbref))
    returnValue(spawned)
