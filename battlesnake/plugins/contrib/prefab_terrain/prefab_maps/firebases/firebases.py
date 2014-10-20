"""
Firebase prefab structures.
"""

from battlesnake.plugins.contrib.prefab_terrain.prefab_maps.base_map_prefab import \
    BaseMapPrefab


class Firebase9x9WalledPrefab(BaseMapPrefab):
    origin = (4, 3)
    map_file = 'firebases/9x9-walled-1.map'


class Firebase11x11WalledPrefab(BaseMapPrefab):
    origin = (5, 6)
    map_file = 'firebases/11x11-walled-1.map'
