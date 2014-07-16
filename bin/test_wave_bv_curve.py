#!/usr/bin/env python
"""
Quick and dirty script sed to output the values for wave BV2.
"""

from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    calc_max_wave_bv2

min_wave_bv2 = 350
opposing_bv2 = 980
difficulty_level = 'normal'

print "Minimum possible BV2", min_wave_bv2
print "Opposing BV2", opposing_bv2
print "Difficulty level", difficulty_level
print "-" * 50
for wave_num in range(1, 10):
    max_bv2 = calc_max_wave_bv2(
        min_wave_bv2, opposing_bv2, difficulty_level, wave_num)
    print "Wave %d: %d" % (wave_num, max_bv2)
