"""
Kill tracking logic.
"""

from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF


def handle_kill(protocol, puppet, victim_unit_dbref, killer_unit_dbref,
                cause_of_death):
    """
    Given a set of details on a kill, figure out how to react and track it.

    :param ArenaMasterPuppet puppet:
    :param str victim_unit_dbref: dbref of the unit that was destroyed.
    :param str killer_unit_dbref: dbref of the killing unit.
    :param str cause_of_death: What caused the victim to die.
    """

    p = protocol
    unit_store = puppet.unit_store

    try:
        victim_unit = unit_store.get_unit_by_dbref(victim_unit_dbref)
    except ValueError:
        victim_unit = None
        print "ERROR: Victim %s not found on @Amechdest!" % victim_unit_dbref
    try:
        killer_unit = unit_store.get_unit_by_dbref(killer_unit_dbref)
    except ValueError:
        killer_unit = None
        print "ERROR: Killer %s not found on @Amechdest!" % killer_unit_dbref

    print "VICTIM", victim_unit
    print "KILLER", killer_unit
    if victim_unit and killer_unit:
        record_kill(p, puppet, victim_unit, killer_unit, cause_of_death)

    # This *has* to happen.
    mux_commands.trigger(p, victim_unit_dbref, 'DESTMECH.T')


def record_kill(protocol, puppet, victim_unit, killer_unit, cause_of_death):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killing unit.
    :param str cause_of_death: What caused the victim to die.
    """

    print "VICTIM", victim_unit.faction_dbref
    if victim_unit.faction_dbref == ATTACKER_FACTION_DBREF:
        announce_attacker_killed(protocol, puppet, victim_unit, killer_unit)
    else:
        announce_defender_killed(protocol, puppet, victim_unit, killer_unit)


def announce_attacker_killed(protocol, puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killing unit.
    """

    attackers = puppet.list_attacking_units()
    attackers = [aunit for aunit in attackers if aunit != victim_unit]
    message = (
        "%ch%cc[name({killer_pilot_dbref})]%cw in "
        "%cc%[{killer_id}%] {killer_mechname}%cw killed "
        "%cy%[{victim_id}%] {victim_mechname}%cw.%r"
        "There are %cr{attackers_left} %cwenemy units remaining.".format(
            killer_pilot_dbref=killer_unit.pilot_dbref,
            killer_id=killer_unit.contact_id,
            killer_mechname=killer_unit.mech_name,
            victim_id=victim_unit.contact_id,
            victim_mechname=victim_unit.mech_name,
            attackers_left=len(attackers))
    )
    puppet.pemit_throughout_zone(protocol, message)


def announce_defender_killed(protocol, puppet, victim_unit, killer_unit):
    """
    :param ArenaMasterPuppet puppet:
    :param ArenaMapUnit victim_unit: The unit that was destroyed.
    :param ArenaMapUnit killer_unit: The killing unit.
    """

    print "DEFENDER EMIT"
    defenders = puppet.list_defending_units()
    defenders = [dunit for dunit in defenders if dunit != victim_unit]
    message = (
        "%ch%cc[name({victim_pilot_dbref})]%cw in "
        "%cc%[{victim_id}%] {victim_mechname}%cw was destroyed by "
        "%cy%[{killer_id}%] {killer_mechname}%cw.%r"
        "There are %cc{defenders_left} %cwfriendly units remaining.".format(
            victim_pilot_dbref=victim_unit.pilot_dbref,
            victim_id=victim_unit.contact_id,
            victim_mechname=victim_unit.mech_name,
            killer_id=killer_unit.contact_id,
            killer_mechname=killer_unit.mech_name,
            defenders_left=len(defenders))
    )
    puppet.pemit_throughout_zone(protocol, message)
