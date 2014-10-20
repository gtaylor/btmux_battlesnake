"""
Functions for generating new wave survival maps.
"""

import random

from btmux_maplib.map_generator.map_generator import MapGenerator
from btmux_maplib.map_generator.heightmap import SimplexHeightHeightMap
from btmux_maplib.map_generator.modifiers.forests import SimplexForestModifier
from btmux_maplib.map_generator.modifiers.mountains import \
    SimplexMountainModifier
from btmux_maplib.map_generator.modifiers.water_limiter import \
    WaterLimiterModifier

from battlesnake.plugins.contrib.prefab_terrain.prefab_maps.firebases.firebases import \
    Firebase11x11WalledPrefab


def generate_new_muxmap():
    """
    For now, we generate a random map with some pretty similar attributes.
    Eventually, we'll break this up a bunch by "climate" and stuff.
    """

    gen = MapGenerator(
        dimensions=(75, 75),
        seed_val=random.random(),
        #seed_val=0.0161681496718,
        heightmap=SimplexHeightHeightMap(),
        modifiers=[
            WaterLimiterModifier(max_water_depth=0),
            # The default values give us numerous, but smaller forest clusters.
            SimplexForestModifier(seed_modifier=0.4),
            # Do a second pass with a different seed and larger forests.
            SimplexForestModifier(
                frequency=40.0, seed_modifier=0.2, light_forest_thresh=0.1,
                heavy_forest_thresh=0.2
            ),
            # We'll make all hexes above elevation 6 in this case, but you can
            # elect to use the defaults for more randomized mountain conversions.
            SimplexMountainModifier(
                mountain_thresh=-1.0, minimum_elevation=6
            ),
        ],
    )
    mmap = gen.generate_map()

    Firebase11x11WalledPrefab.place(
        mmap, mmap.get_map_width() / 2, mmap.get_map_height() / 2)

    return mmap
