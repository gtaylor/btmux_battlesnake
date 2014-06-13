from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.puppets.units.unit_store import \
    ArenaMapUnitStore
from battlesnake.plugins.contrib.arena_master.puppets.strategic_logic import \
    move_idle_units


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, protocol, dbref, map_dbref, map_height, map_width):
        self.protocol = protocol
        self.dbref = dbref
        self.map_dbref = map_dbref
        # A cache for all units in the arena, plus their states.
        self.unit_store = ArenaMapUnitStore(self)
        # This is the faction that the arena puppet has control of.
        self.attacking_faction_dbref = ATTACKER_FACTION_DBREF
        # And our protagonists.
        self.defending_faction_dbref = DEFENDER_FACTION_DBREF
        self.map_height = int(map_height)
        self.map_width = int(map_width)

    def __str__(self):
        return u"<ArenaMasterPuppet: %s for map %s>" % (self.dbref, self.map_dbref)

    def do_strategic_tic(self):
        """
        For now, we use smallish maps and get the AI to stumble into the
        defenders. We could get smarter and more precise down the road,
        but this will do for now.
        """

        units_by_faction = self.unit_store.list_units_by_faction()
        attacking_units = units_by_faction.get(self.attacking_faction_dbref, [])
        #defending_units = units_by_faction.get(self.defending_faction_dbref, [])

        attacking_ai_units = [unit for unit in attacking_units if unit.is_ai]
        # Put any slackers to work roaming around.
        move_idle_units(self, attacking_ai_units)
