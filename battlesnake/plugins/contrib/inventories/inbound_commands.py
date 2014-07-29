from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.core.ansi import ANSI_NORMAL, \
    ANSI_HI_GREEN, ANSI_HI_YELLOW, ANSI_HI_RED, ANSI_HI_MAGENTA, ANSI_HI_CYAN, \
    ANSI_HI_WHITE
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers

from battlesnake.plugins.contrib.inventories.api import modify_player_inventory, \
    get_player_inventory
from battlesnake.plugins.contrib.inventories.defines import ITEM_TYPES, \
    ITEM_TYPE_WEAPON, ITEM_TYPE_MELEE_WEAPON, ITEM_TYPE_PART, ITEM_TYPE_COMMOD


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


class ItemsCommand(BaseCommand):
    """
    Lists a player's iteminventory.
    """

    command_name = "inv_items"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="items", description='Lists all of your parts/weapons.')

        parser.add_argument(
            "item_type", type=str, choices=ITEM_TYPES, default=None,
            nargs='?', help="Item types to list")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        pval = self._get_header_str('Item Listing', width=73)
        pval += '%r%b%b'

        items = yield get_player_inventory(
            invoker_dbref, type_filter=args.item_type)
        for counter, item in enumerate(items, start=1):
            itype = item['item_type']
            if itype == ITEM_TYPE_MELEE_WEAPON:
                itype_color = ANSI_HI_MAGENTA
            elif itype == ITEM_TYPE_WEAPON:
                itype_color = ANSI_HI_RED
            elif itype == ITEM_TYPE_PART:
                itype_color = ANSI_HI_WHITE
            elif itype == ITEM_TYPE_COMMOD:
                itype_color = ANSI_HI_CYAN
            else:
                raise ValueError("Invalid item_type: %s" % itype)
            pval += (
                "[ljust("
                "  [ljust({itype_color}{item_name}{ansi_normal},25,.)]"
                "  {quantity}"
                ", 35)]".format(
                item_name=item['item_id'], quantity=item['quantity'],
                itype_color=itype_color,
                ansi_normal=ANSI_NORMAL,
            ))
            if counter % 2 == 0:
                pval += "%r%b%b"

        pval += self._get_footer_str(pad_char='-', width=73)
        pval += '%r[space(5)]'
        pval += '[ljust(%ch%chPart,18)]'
        pval += '[ljust(%ch%crWeapon, 18)]'
        pval += '[ljust(%ch%cmMelee Weapon, 18)]'
        pval += '%ch%ccCommodity'
        pval += '%r[space(22)]%cnFor more info, type %ch%cgitems -h%cn'
        pval += self._get_footer_str(width=73)
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class InventoriesCommandTable(InboundCommandTable):

    commands = [
        ModInventoryCommand,
        ItemsCommand
    ]
