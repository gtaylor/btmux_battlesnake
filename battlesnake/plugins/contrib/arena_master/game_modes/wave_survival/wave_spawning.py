import math
import random

from twisted.internet.defer import inlineCallbacks, returnValue
from battlesnake.outbound_commands.think_fn_wrappers import get_map_dimensions
from battlesnake.plugins.contrib.ai.outbound_commands import start_unit_ai
from battlesnake.plugins.contrib.factions.api import get_faction
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF

from battlesnake.plugins.contrib.pg_db.api import get_db_connection

# All of our max wave BV2 values are based off of this starter value. This
# assumes one player on wave one with a 1.0 difficulty mod (normal difficulty).
# From here, we multiply based on all of those previously mentioned variables.
from battlesnake.plugins.contrib.unit_spawning.outbound_commands import \
    create_unit


@inlineCallbacks
def pick_refs_for_wave(wave_num, opposing_bv2, difficulty_modifier):
    """
    :param int wave_num: A wave number. Starting at 1.
    :param int opposing_bv2: The total BV2 for the opposing force.
    :param float difficulty_modifier: A difficulty modifier that reduces
        the BV. Values 0...1
    :rtype: list
    :returns: A list of unit ref strings to spawn for this wave.
    """

    print "OPPOSING BV2", opposing_bv2
    first_wave_bv2 = opposing_bv2 * difficulty_modifier
    # Successive waves are slightly harder than the first wave.
    max_wave_bv2 = first_wave_bv2 + (first_wave_bv2 * math.log(wave_num))
    print "MAX WAVE BV2", max_wave_bv2

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
def spawn_wave(protocol, wave_num, opposing_bv2, difficulty_modifier,
               arena_master_puppet):
    """
    Spawns a wave of attackers.

    :param BattlesnakeTelnetProtocol protocol:
    :param int wave_num: The wave number to spawn. Higher waves are
        more difficult.
    :param int opposing_bv2: The total BV2 for the opposing force.
    :param float difficulty_modifier: 1.0 = moderate difficulty,
        anything less is easier, anything more is harder.
    :param ArenaMasterPuppet arena_master_puppet: The arena master puppet
        instance to spawn through.
    :rtype: list
    :returns: A list of tuples containing details on the spawned units.
        Tuples are in the form of (unit_ref, unit_dbref).
    """

    map_dbref = arena_master_puppet.map_dbref
    map_width, map_height = yield get_map_dimensions(protocol, map_dbref)
    refs = yield pick_refs_for_wave(wave_num, opposing_bv2, difficulty_modifier)
    faction = get_faction(ATTACKER_FACTION_DBREF)
    spawned = []
    for unit_ref in refs:
        unit_x, unit_y = choose_unit_spawn_spot(map_width, map_height)
        unit_dbref = yield create_unit(
            protocol, unit_ref, map_dbref, faction, unit_x, unit_y,
            zone_dbref=arena_master_puppet.dbref)
        start_unit_ai(protocol, unit_dbref)
        spawned.append((unit_ref, unit_dbref))
    returnValue(spawned)
