"""
Kill tracking logic.
"""

from twisted.internet.defer import inlineCallbacks

from battlesnake.plugins.contrib.arena_master.db_api import record_kill_in_db
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF


@inlineCallbacks
def record_kill(puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killer unit.
    """

    yield record_kill_in_db(puppet, victim_unit, killer_unit)


def announce_death(puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killer unit.
    """

    if victim_unit == killer_unit:
        # May have been spewed on, an ammo boom, or something suicidal.
        announce_ambiguous_death(puppet, victim_unit)
    elif victim_unit.faction_dbref == ATTACKER_FACTION_DBREF:
        announce_attacker_killed(puppet, victim_unit, killer_unit)
    else:
        announce_defender_killed(puppet, victim_unit, killer_unit)


def announce_ambiguous_death(puppet, destroyed_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit destroyed_unit: The unit that was destroyed.
    """

    if destroyed_unit.faction_dbref == ATTACKER_FACTION_DBREF:
        unit_color = "%cy"
    else:
        unit_color = "%cc"

    if destroyed_unit.is_ai:
        message = (
            "%ch{unit_color}%[{victim_id}%] {victim_mechname}%cw "
            "has been destroyed.".format(
                victim_id=destroyed_unit.contact_id,
                victim_mechname=destroyed_unit.mech_name,
                unit_color=unit_color))
    else:
        message = (
            "%ch{unit_color}[name({victim_pilot_dbref})]%cw in "
            "{unit_color}%[{victim_id}%] {victim_mechname}%cw "
            "has been destroyed.".format(
                victim_pilot_dbref=destroyed_unit.pilot_dbref,
                victim_id=destroyed_unit.contact_id,
                victim_mechname=destroyed_unit.mech_name,
                unit_color=unit_color))

    puppet.pemit_throughout_zone(message)
    puppet.announce_num_units_remaining(exclude_unit=destroyed_unit)


def announce_attacker_killed(puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killing unit.
    """

    message = (
        "%ch%cc[name({killer_pilot_dbref})]%cw in "
        "%cc%[{killer_id}%] {killer_mechname}%cw killed "
        "%cy%[{victim_id}%] {victim_mechname}%cw.".format(
            killer_pilot_dbref=killer_unit.pilot_dbref,
            killer_id=killer_unit.contact_id,
            killer_mechname=killer_unit.mech_name,
            victim_id=victim_unit.contact_id,
            victim_mechname=victim_unit.mech_name)
    )
    puppet.pemit_throughout_zone(message)


def announce_defender_killed(puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killing unit.
    """

    message = (
        "%ch%cy%[{killer_id}%] {killer_mechname}%cw has destroyed "
        "%cc[name({victim_pilot_dbref})]%cw in "
        "%cc%[{victim_id}%] {victim_mechname}%cw.".format(
            victim_pilot_dbref=victim_unit.pilot_dbref,
            victim_id=victim_unit.contact_id,
            victim_mechname=victim_unit.mech_name,
            killer_id=killer_unit.contact_id,
            killer_mechname=killer_unit.mech_name)
    )
    puppet.pemit_throughout_zone(message)
