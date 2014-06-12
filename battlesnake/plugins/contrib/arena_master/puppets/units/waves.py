import math

from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.plugins.contrib.pg_db.api import get_db_connection

# All of our max wave BV2 values are based off of this starter value. This
# assumes one player on wave one with a 1.0 difficulty mod (normal difficulty).
# From here, we multiply based on all of those previously mentioned variables.
BASE_FIRST_WAVE_BV2 = 600


@inlineCallbacks
def pick_refs_for_wave(wave_num, num_players, difficulty_modifier):
    """
    :param int wave_num: A wave number. Starting at 1.
    :param int num_players: The number of players on the defending team.
    :param float difficulty_modifier: A difficulty modifier that reduces
        the BV. Values 0...1
    :rtype: list
    :returns: A list of unit ref strings to spawn for this wave.
    """

    first_wave_bv2 = BASE_FIRST_WAVE_BV2 * num_players * difficulty_modifier
    max_wave_bv2 = first_wave_bv2 + (first_wave_bv2 * math.log(wave_num))

    conn = yield get_db_connection()
    results = yield conn.runQuery(
        'SELECT reference, battle_value2 FROM unit_library_unit '
        '  WHERE battle_value2<=%s ORDER BY random()',
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
