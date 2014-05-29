"""
Static constants that are faction-related.
"""

from battlesnake.plugins.contrib.factions.faction_obj import Faction

ATTACKER_FACTION_DBREF = '#94'
DEFENDER_FACTION_DBREF = '#91'

FACTIONS = {
    DEFENDER_FACTION_DBREF: Faction(DEFENDER_FACTION_DBREF, 'Defenders'),
    ATTACKER_FACTION_DBREF: Faction(ATTACKER_FACTION_DBREF, 'Attackers'),
}
