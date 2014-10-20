import os

from btmux_maplib.map_parser.fileobj import MapFileObjParser


class BaseMapPrefab(object):
    """
    A map file-based prefab.
    """

    MAP_PATH = os.path.dirname(os.path.abspath(__file__))
    # Set this in your sub-class. Relative to this module's directory.
    map_file = None
    # The hex on the prefab that will be the center hex on the MuxMap.
    origin = (0, 0)

    @classmethod
    def place(cls, mmap, pf_x, pf_y, decliffe_edges=True):
        """
        Places the prefab map on the given MuxMap instance. MuxMap is
        modified in-place.

        :param MuxMap mmap:
        :param int pf_x: Where to place the prefab structure on the MuxMap.
        :param int pf_y: Where to place the prefab structure on the MuxMap.
        :keyword bool decliffe_edges: If True, try to smooth the edges up
            in order to lessen cliffs.
        """

        pf_map = cls._get_prefab_mmap()
        start_x, start_y = cls._determine_start_hex(pf_x, pf_y)
        base_elev = cls._calc_base_prefab_elev(mmap, pf_map, start_x, start_y)

        for y in range(0, pf_map.get_map_height()):
            for x in range(0, pf_map.get_map_width()):
                mmap_x = start_x + x
                mmap_y = start_y + y
                if not cls._coord_is_inbounds(mmap, mmap_x, mmap_y):
                    continue

                mmap.set_hex(
                    mmap_x, mmap_y,
                    terrain=pf_map.terrain_list[y][x],
                    elevation=pf_map.elevation_list[y][x] + base_elev
                )
        if decliffe_edges:
            cls._decliff_edges(mmap, pf_map, start_x, start_y)

    @classmethod
    def _decliff_edges(cls, mmap, pf_map, start_x, start_y):
        """
        Super shitty, but eh. It'll do for now.
        """

        # Upper boundary
        for x in range(0, pf_map.get_map_width()):
            pf_x = start_x + x
            pf_y = start_y
            edge_x = pf_x
            edge_y = pf_y - 1
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y)
            if pf_x % 2 == 0:
                cls._defcliff_hex_pair(mmap, pf_x, pf_y + 1, edge_x, edge_y)
                cls._defcliff_hex_pair(mmap, pf_x, pf_y - 1, edge_x, edge_y)

        # Lower boundary
        for x in range(0, pf_map.get_map_width()):
            pf_x = start_x + x
            pf_y = start_y + pf_map.get_map_height() - 1
            edge_x = pf_x
            edge_y = pf_y + 1
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y)
            if pf_x % 2 == 0:
                cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x + 1, edge_y)
                cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x - 1, edge_y)

        # Left boundary
        for y in range(0, pf_map.get_map_height()):
            pf_x = start_x
            pf_y = start_y + y
            edge_x = pf_x - 1
            edge_y = pf_y
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y)
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y - 1)

        # Right boundary
        for y in range(0, pf_map.get_map_height()):
            pf_x = start_x + pf_map.get_map_width() - 1
            pf_y = start_y + y
            edge_x = pf_x + 1
            edge_y = pf_y
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y)
            cls._defcliff_hex_pair(mmap, pf_x, pf_y, edge_x, edge_y - 1)

    @classmethod
    def _defcliff_hex_pair(cls, mmap, pf_x, pf_y, edge_x, edge_y):
        """
        Given a prefab hex and an edge hex, figure out if the edge
        hex is too high/low and modify as need be.
        """

        if not cls._coord_is_inbounds(mmap, edge_x, edge_y):
            return
        edge_terrain = mmap.terrain_list[edge_y][edge_x]
        if edge_terrain == '~':
            # TODO: Handle water.
            return
        edge_elev = mmap.elevation_list[edge_y][edge_x]
        pf_elev = mmap.elevation_list[pf_y][pf_x]
        edge_diff = pf_elev - edge_elev
        if edge_diff > 2:
            # Edge is too low. Bring it up as little as we can.
            mmap.elevation_list[edge_y][edge_x] = pf_elev - 2
        elif edge_diff < -2:
            # Edge is too high. Go as high as we can.
            mmap.elevation_list[edge_y][edge_x] = pf_elev + 2

    @classmethod
    def _get_prefab_mmap(cls):
        """
        :rtype: MuxMap
        """

        prefab_path = os.path.join(cls.MAP_PATH, cls.map_file)
        parser = MapFileObjParser(open(prefab_path, 'r'))
        return parser.get_muxmap()

    @classmethod
    def _coord_is_inbounds(cls, mmap, x, y):
        """
        :rtype: bool
        :returns: True if the given hex is inbounds on the map in question.
        """

        if x < 0 or y < 0:
            return False
        elif x > mmap.get_map_width() - 1:
            return False
        elif y > mmap.get_map_height() - 1:
            return False
        return True

    @classmethod
    def _calc_base_prefab_elev(cls, mmap, pf_map, start_x, start_y):
        # TODO: We could do this much more efficiently if we cared to.
        hex_count = 0
        elev_sum = 0

        # We just check the rows on the very top and bottom of where the
        # prefab will be placed on the map. Not good for anything super
        # oblong, but will do for now.
        for y in [0, pf_map.get_map_height() - 1]:
            for x in range(0, pf_map.get_map_width()):
                mmap_x = start_x + x
                mmap_y = start_y + y
                if not cls._coord_is_inbounds(mmap, mmap_x, mmap_y):
                    continue
                elev_sum += mmap.elevation_list[mmap_y][mmap_x]
                hex_count += 1

        return elev_sum / hex_count

    @classmethod
    def _determine_start_hex(cls, pf_x, pf_y):
        origin_x, origin_y = cls.origin
        start_x = pf_x - origin_x
        start_y = pf_y - origin_y
        return start_x, start_y
