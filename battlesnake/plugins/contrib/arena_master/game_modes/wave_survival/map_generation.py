"""
Functions for generating new wave survival maps.
"""

import random

from btmux_maplib.map_generator.map_generator import MapGenerator
from btmux_maplib.map_generator.heightmap import SimplexHeightHeightMap
from btmux_maplib.map_generator.modifiers.water_limiter import \
    WaterLimiterModifier


def generate_new_muxmap():

    gen = MapGenerator(
        dimensions=(75, 75),
        seed_val=random.random(),
        #seed_val=0.0161681496718,
        heightmap=SimplexHeightHeightMap(),
        modifiers=[
            WaterLimiterModifier(max_water_depth=0),
        ],
    )
    return gen.generate_map()
