from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.plugins.contrib.inventories.api import modify_player_inventory


class ModInventoryCommand(BaseCommand):
    """
    Modifies (adds or removes) econ items from a player's inventory.
    """

    command_name = "inv_modinv"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        print parsed_line.kwargs
        player_dbref = parsed_line.kwargs['player_dbref']
        econ_item = parsed_line.kwargs['econ_item']
        mod_amount = int(parsed_line.kwargs['mod_amount'])

        if mod_amount == 0:
            raise CommandError("0 is an invalid value for modding.")
        elif mod_amount < 0:
            verb = "Removing"
            modifier = "from"
        else:
            verb = "Adding"
            modifier = "to"

        message = (
            "{verb} {mod_amount} {econ_item}s {modifier} "
            "[name({player_dbref})]%({player_dbref}%)'s inventory.".format(
                verb=verb, mod_amount=mod_amount, econ_item=econ_item,
                modifier=modifier, player_dbref=player_dbref))
        mux_commands.pemit(protocol, invoker_dbref, message)

        new_balance = yield modify_player_inventory(
            player_dbref, econ_item, mod_amount)
        message = "New balance: %d" % new_balance
        mux_commands.pemit(protocol, invoker_dbref, message)


class InventoriesCommandTable(InboundCommandTable):

    commands = [
        ModInventoryCommand,
    ]
