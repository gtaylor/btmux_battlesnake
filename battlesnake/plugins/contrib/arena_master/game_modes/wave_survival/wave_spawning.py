import random

from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions
from battlesnake.plugins.contrib.ai.outbound_commands import start_unit_ai
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.defines import \
    WAVE_DIFFICULTY_LEVELS, MIN_WAVE_BV2
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF
from battlesnake.plugins.contrib.pg_db.api import get_db_connection
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


def calc_max_wave_bv2(min_wave_bv2, defender_bv2, difficulty_level, wave_num):
    """
    Given a set of parameters, calculate the maximum total BV2 of the attacking
    force for the given wave.

    :param int min_wave_bv2: The floor for the BV2 total. Prevents us from
        creating an un-spawnable wave if the difficulty modifier drags us
        too low.
    :param int defender_bv2: The BV2 total for all defending units.
    :param str difficulty_level: The name of the difficulty level.
    :param int wave_num: The wave number.
    :rtype: int
    :returns: The max BV2 for the wave.
    """

    wave_diff_defines = WAVE_DIFFICULTY_LEVELS[difficulty_level]
    difficulty_modifier = wave_diff_defines['modifier']
    wave_step = wave_diff_defines['wave_step']

    # Subtract by one to make sure that we start at the base BV2 for the
    # defending force at wave 1.
    z_wave_num = wave_num - 1
    #y=(bv * diff) + ((bv * wave_step) * wave_num)
    # Start with the defender BV2 total, modified by the difficulty modifier.
    bv2 = defender_bv2 * difficulty_modifier
    # Add the wave-induced difficulty ramp-up. This ends up being a percentage
    # of the defender BV2, the wave_step.
    bv2 += defender_bv2 * wave_step * z_wave_num
    # Cap the lowest possible BV2 to make sure the wave is always spawnable.
    return max(min_wave_bv2, bv2)


@inlineCallbacks
def pick_refs_for_wave(wave_num, opposing_bv2, difficulty_level):
    """
    :param int wave_num: A wave number. Starting at 1.
    :param int opposing_bv2: The total BV2 for the opposing force.
    :param str difficulty_level: The difficulty level name.
    :rtype: list
    :returns: A list of unit ref strings to spawn for this wave.
    """

    print "Total Defender BV2", opposing_bv2
    max_wave_bv2 = calc_max_wave_bv2(
        MIN_WAVE_BV2, opposing_bv2, difficulty_level, wave_num)
    print "Max Attacker BV2", max_wave_bv2

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT reference, battle_value2 FROM unit_library_unit '
        '  WHERE is_ai_spawnable=True AND battle_value2<=%s ORDER BY random()',
        (max_wave_bv2,)
    )

    wave_bv = 0
    refs = []
    for row in results:
        if wave_bv > max_wave_bv2:
            break

        bv2 = row['battle_value2']
        if bv2 + wave_bv > max_wave_bv2:
            continue

        refs.append(row['reference'])
        wave_bv += row['battle_value2']

    returnValue(refs)


def choose_unit_spawn_spot(map_width, map_height):
    """
    :param int map_width: The 1-indexed width of the map.
    :param int map_height: The 1-indexed height of the map.
    :rtype: tuple
    :returns: A tuple of x,y coordinates for a unit to spawn at.
    """

    x = 0
    y = 0
    padding = 5
    spawn_side = random.choice(['left', 'right', 'top', 'bottom'])
    if spawn_side == 'left':
        x = random.randrange(0, padding)
    elif spawn_side == 'right':
        x = random.randrange(map_width - padding, map_width)
    if spawn_side in ['left', 'right']:
        y = random.randrange(0, map_height)

    if spawn_side == 'top':
        y = random.randrange(0, padding)
    elif spawn_side == 'bottom':
        y = random.randrange(map_height - padding, map_height)
    if spawn_side in ['top', 'bottom']:
        x = random.randrange(0, map_width)

    return x, y


@inlineCallbacks
def spawn_wave(protocol, wave_num, opposing_bv2, difficulty_level,
               arena_master_puppet):
    """
    Spawns a wave of attackers.

    :param BattlesnakeTelnetProtocol protocol:
    :param int wave_num: The wave number to spawn. Higher waves are
        more difficult.
    :param int opposing_bv2: The total BV2 for the opposing force.
    :param str difficulty_level: The difficulty level name.
    :param ArenaMasterPuppet arena_master_puppet: The arena master puppet
        instance to spawn through.
    :rtype: list
    :returns: A list of tuples containing details on the spawned units.
        Tuples are in the form of (unit_ref, unit_dbref).
    """

    wave_diff_defines = WAVE_DIFFICULTY_LEVELS[difficulty_level]
    ai_gunnery = wave_diff_defines['ai_gunnery_skills']
    ai_piloting = wave_diff_defines['ai_piloting_skills']
    map_dbref = arena_master_puppet.map_dbref
    map_width, map_height = yield get_map_dimensions(protocol, map_dbref)
    refs = yield pick_refs_for_wave(wave_num, opposing_bv2, difficulty_level)
    faction = get_faction(ATTACKER_FACTION_DBREF)

    spawned = []
    for unit_ref in refs:
        unit_x, unit_y = choose_unit_spawn_spot(map_width, map_height)
        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction, unit_x, unit_y,
            zone_dbref=arena_master_puppet.dbref)
        start_unit_ai(
            protocol, unit_dbref, piloting_skill=ai_piloting,
            gunnery_skill=ai_gunnery)
        spawned.append((unit_ref, unit_dbref))
    returnValue(spawned)
