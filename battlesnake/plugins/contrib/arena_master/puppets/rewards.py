import random
from collections import deque

from twisted.internet.defer import inlineCallbacks

from battlesnake.outbound_commands import mux_commands
from battlesnake.plugins.contrib.factions.defines import ATTACKER_FACTION_DBREF, \
    DEFENDER_FACTION_DBREF

from battlesnake.plugins.contrib.arena_master.db_api import \
    get_wave_salvage_from_db, get_wave_participants_from_db
from battlesnake.plugins.contrib.inventories.blueprints_api import \
    reward_random_blueprint
from battlesnake.plugins.contrib.inventories.items_api import modify_player_item_inventory


@inlineCallbacks
def reward_blueprints_to_participants(protocol, wave_id, draw_chance):
    """
    Gives each wave participant a shot at drawing a blueprint.

    :param int wave_id: ID of the wave in the DB.
    :param int draw_chance: A number 0-100 that determines the percent
        chance that a player will draw some kind of blueprint.
    """

    p = protocol
    defender_faction_id = int(DEFENDER_FACTION_DBREF[1:])
    participants = yield get_wave_participants_from_db(
        wave_id, defender_faction_id)
    for participant in participants:
        player_dbref = "#%s" % participant['pilot_id']
        yield reward_random_blueprint(p, player_dbref, draw_chance)


def divide_salvage(salvage_dict, num_divisions, salvage_loss):
    """
    Given a dict of salvage to split, divide it up ``num_divisions`` way.
    This is done by taking turns, with a chance to lose your turn entirely
    with a bad roll (thus taking a certain quantity of salvage out of play).

    :param dict salvage_dict: The salvage to split. Keys are item names,
        values are quantity.
    :param int num_divisions: The number of ways to split the salvage.
    :param int salvage_loss: A number 0-100 that determines the percent
        chance that a salvage turn will be lost. 90 = 90% chance, etc.
    :rtype: list
    :returns: A list of salvage dicts, divided up semi-randomly.
    """

    # This will hold our divided salvage dict.
    divided = {k: {} for k in range(0, num_divisions)}
    # Keeps track of whose turn it is to draw salvage.
    turn_tracker = deque(range(0, num_divisions))

    for iname, iremaining in salvage_dict.items():
        if iname.startswith('Ammo_'):
            continue
        while iremaining > 0:
            who = turn_tracker.popleft()
            turn_tracker.append(who)
            num_awarded = random.randint(0, iremaining)
            if num_awarded == 0:
                # Bummer, dude.
                continue
            if random.randint(0, 100) <= salvage_loss:
                # Randomly discarded. Ouch.
                iremaining -= num_awarded
                continue
            if iname not in divided[who]:
                divided[who][iname] = num_awarded
            else:
                divided[who][iname] += num_awarded
            iremaining -= num_awarded

    return divided.values()


@inlineCallbacks
def reward_salvage_for_wave(protocol, wave_id, salvage_loss):
    """
    Split the salvage up among the victors of a wave.

    :param int wave_id: ID of the wave in the DB.
    :param int salvage_loss: A number 0-100 that determines the percent
        chance that a salvage turn will be lost. 90 = 90% chance, etc.
    """

    # This is hardcoded for now.
    loser_faction_id = int(ATTACKER_FACTION_DBREF[1:])
    defender_faction_id = int(DEFENDER_FACTION_DBREF[1:])
    # Query all of the losing faction's Participants in the DB. See what
    # parts were intact when the unit was destroyed.
    salvage_dicts = yield get_wave_salvage_from_db(wave_id, loser_faction_id)
    # This dict will hold the combined salvage from all units.
    combined_salvage = {}

    for sdict in salvage_dicts:
        for iname, icount in sdict.items():
            if iname not in combined_salvage:
                combined_salvage[iname] = int(icount)
            else:
                combined_salvage[iname] += int(icount)

    participants = yield get_wave_participants_from_db(wave_id, defender_faction_id)
    num_divisions = len(participants)
    # Salvage is now divided up into a list of dicts matching each participant.
    split_salvage = divide_salvage(combined_salvage, num_divisions, salvage_loss)

    for pcount, psalvage in enumerate(split_salvage):
        player_id = participants[pcount]['pilot_id']
        yield reward_salvage_to_player(protocol, psalvage, player_id)


@inlineCallbacks
def reward_salvage_to_player(protocol, salvage, player_id):
    """
    Given a dict of salvage, set it all on the player's inventory and
    emit the reward.

    :param dict salvage: A dict of salvage. Keys are part names, values are
        quantities. Part names must match what's in the DB exactly, case
        and all.
    :param int player_id: The player's ID (not dbref). This is just dbref
        as an int sands pound sign.
    """

    player_dbref = "#%s" % player_id
    print "PLAYER", player_dbref
    print "SALVAGE", salvage
    if not salvage:
        return
    yield modify_player_item_inventory(player_dbref, salvage)

    message = "%chYou have been awarded salvage for your participation:%cn"
    for iname, icount in salvage.items():
        message += "%r [rjust(%ch%cc{icount},3)]%cn%ccx%cn {iname}".format(
            icount=icount, iname=iname)
    message += "%r%chType %ch%cgitems%cw to see your full inventory.%cn"
    mux_commands.pemit(protocol, player_dbref, message)
