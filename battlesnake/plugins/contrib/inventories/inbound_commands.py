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
from battlesnake.plugins.contrib.inventories.blueprints_api import \
    modify_player_blueprint_inventory, get_player_blueprint_inventory, \
    reward_random_blueprint
from battlesnake.plugins.contrib.inventories.cbill_api import \
    mod_player_cbill_balance, get_player_cbill_balance

from battlesnake.plugins.contrib.inventories.items_api import modify_player_item_inventory, \
    get_player_item_inventory
from battlesnake.plugins.contrib.inventories.defines import ITEM_TYPES, \
    ITEM_TYPE_WEAPON, ITEM_TYPE_MELEE_WEAPON, ITEM_TYPE_PART, ITEM_TYPE_COMMOD
from battlesnake.plugins.contrib.inventories.units_api import \
    get_player_unit_summary_list
from battlesnake.plugins.contrib.unit_library.api import get_unit_by_ref, \
    get_weight_class_color_for_tonnage


class ModItemInventoryCommand(BaseCommand):
    """
    Modifies (adds or removes) econ items from a player's item inventory.
    """

    command_name = "inv_moditem"

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

        modded_dict = {
            econ_item: mod_amount,
        }

        new_balance = yield modify_player_item_inventory(player_dbref, modded_dict)
        message = "New balance: %s" % new_balance
        mux_commands.pemit(protocol, invoker_dbref, message)


class ModBlueprintInventoryCommand(BaseCommand):
    """
    Modifies (adds or removes) econ items from a player's blueprint inventory.
    """

    command_name = "inv_modbp"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        print parsed_line.kwargs
        player_dbref = parsed_line.kwargs['player_dbref']
        unit_ref = parsed_line.kwargs['unit_ref']
        bp_type = parsed_line.kwargs['bp_type']
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
            "{verb} {mod_amount} {bp_type} {unit_ref} blueprint(s) {modifier} "
            "[name({player_dbref})]%({player_dbref}%)'s inventory.".format(
                verb=verb, mod_amount=mod_amount, unit_ref=unit_ref,
                bp_type=bp_type, modifier=modifier, player_dbref=player_dbref))
        mux_commands.pemit(protocol, invoker_dbref, message)

        bp_mods = [
            {'unit_ref': unit_ref, 'bp_type': bp_type, 'mod_amount': mod_amount},
        ]

        new_balance = yield modify_player_blueprint_inventory(
            player_dbref, bp_mods)
        message = "New balance: %s" % new_balance
        mux_commands.pemit(protocol, invoker_dbref, message)


class ModCbillsCommand(BaseCommand):
    """
    Modifies (adds or removes) cbills from a player's inventory.
    """

    command_name = "inv_modcbills"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        print parsed_line.kwargs
        player_dbref = parsed_line.kwargs['player_dbref']
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
            "{verb} {mod_amount} cbills {modifier} "
            "[name({player_dbref})]%({player_dbref}%)'s inventory.".format(
                verb=verb, mod_amount=mod_amount, modifier=modifier,
                player_dbref=player_dbref))
        mux_commands.pemit(protocol, invoker_dbref, message)

        new_balance = yield mod_player_cbill_balance(
            player_dbref, mod_amount)
        message = "New balance: %s" % new_balance
        mux_commands.pemit(protocol, invoker_dbref, message)


class ItemsCommand(BaseCommand):
    """
    Lists a player's item inventory.
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
        pval = self._get_header_str('Item Inventory Listing', width=73)
        pval += (
            "%r%b%b[ljust(%chItem,25)]"
            "[ljust(%chQty,10)]"
            "[ljust(%chItem,25)]"
            "%chQty"
        )
        pval += self._get_footer_str(pad_char='-', width=73)
        pval += '%r%b%b'

        items = yield get_player_item_inventory(
            invoker_dbref, type_filter=args.item_type)
        total_items = len(items)
        for counter, item in enumerate(items, start=1):
            itype = item['item_type']
            if itype == ITEM_TYPE_MELEE_WEAPON:
                itype_color = ANSI_HI_MAGENTA
            elif itype == ITEM_TYPE_WEAPON:
                itype_color = ANSI_HI_RED
            elif itype == ITEM_TYPE_PART:
                itype_color = ANSI_HI_YELLOW
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
                ansi_normal=ANSI_NORMAL))
            if counter % 2 == 0 and counter != total_items:
                pval += "%r%b%b"
        if not items:
            pval += "[center(You have no items yet. Get to the arena!,78)]"

        pval += self._get_footer_str(pad_char='-', width=73)
        pval += '%r[space(5)]'
        pval += '[ljust(%ch%cyPart,18)]'
        pval += '[ljust(%ch%crWeapon, 18)]'
        pval += '[ljust(%ch%cmMelee Weapon, 18)]'
        pval += '%ch%ccCommodity'
        pval += '%r[space(22)]%cnFor more info, type %ch%cgitems -h%cn'
        pval += self._get_footer_str(width=73)
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class BlueprintsCommand(BaseCommand):
    """
    Lists a player's blueprint inventory.
    """

    command_name = "inv_blueprints"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="blueprints", description='Lists all of your unit blueprints.')

        parser.add_argument(
            "unit_ref", type=str, default=None,
            nargs='?', help="Blueprints for a single unit")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        pval = self._get_header_str('Blueprint Inventory Listing', width=73)
        pval += (
            "%r [ljust(%chUnit Ref.,17)]"
            "[ljust(%ch%cgStructural,12)]"
            "[ljust(%ch%ccElectronics,15)]"
            "[ljust(%ch%cmWeaponry,14)]"
            "%cw%chComplete set?%cn"
        )
        pval += self._get_footer_str(width=73, pad_char='-')
        if args.unit_ref:
            try:
                yield get_unit_by_ref(args.unit_ref)
            except ValueError:
                raise CommandError("Invalid reference.")

        bps = yield get_player_blueprint_inventory(
            invoker_dbref, unit_ref=args.unit_ref)
        for unit_ref, bp_dict in bps.items():
            num_structural = bp_dict.get('structural', 0)
            structural_color = ANSI_NORMAL if num_structural > 0 else ANSI_HI_RED
            structural_str = "{color}{num_structural}".format(
                color=structural_color, num_structural=num_structural)

            num_electronics = bp_dict.get('electronics', 0)
            electronics_color = ANSI_NORMAL if num_electronics > 0 else ANSI_HI_RED
            electronics_str = "{color}{num_electronics}".format(
                color=electronics_color, num_electronics=num_electronics)

            num_weaponry = bp_dict.get('weaponry', 0)
            weaponry_color = ANSI_NORMAL if num_weaponry > 0 else ANSI_HI_RED
            weaponry_str = "{color}{num_weaponry}".format(
                color=weaponry_color, num_weaponry=num_weaponry)

            if num_structural > 0 and num_weaponry > 0 and num_electronics > 0:
                buildable_str = "{color}Complete{ansi_normal}".format(
                    color=ANSI_HI_GREEN, ansi_normal=ANSI_NORMAL)
            else:
                buildable_str = "{color}Incomplete{ansi_normal}".format(
                    color=ANSI_HI_RED, ansi_normal=ANSI_NORMAL)

            pval += "%r%b"
            pval += (
                "[ljust({ref_color}{unit_ref}{ansi_normal}%b,20,.)] "
                "[ljust(%ch%cgS:%cn {structural}%b,12,.)]"
                "%b[ljust(%ch%ccE:%cn {electronics}%b,12,.)]"
                "%b[ljust(%ch%cmW:%cn {weaponry}%b,10,.)]"
                "%b{buildable}".format(
                    ref_color=ANSI_HI_WHITE, unit_ref=unit_ref,
                    structural=structural_str, electronics=electronics_str,
                    weaponry=weaponry_str, buildable=buildable_str,
                    ansi_normal=ANSI_NORMAL))
        if not bps:
            pval += "%r[center(You have no blueprints yet. Get to the arena!,78)]"

        pval += self._get_footer_str(width=73, pad_char='-')
        pval += '%r[space(20)]%cnFor more info, type %ch%cgblueprints -h%cn'
        pval += self._get_footer_str(width=73)
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class RewardBpCommand(BaseCommand):
    """
    Modifies (adds or removes) econ items from a player's item inventory.
    """

    command_name = "inv_rewardbp"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        print parsed_line.kwargs
        player_dbref = parsed_line.kwargs['player_dbref']
        draw_chance = int(parsed_line.kwargs['draw_chance'])

        bp_ref, bp_type = yield reward_random_blueprint(
            protocol, player_dbref, draw_chance)
        if bp_ref:
            pval = "[name({player_dbref})] draws a {bp_ref} {bp_type} blueprint".format(
                player_dbref=player_dbref, bp_ref=bp_ref, bp_type=bp_type)
        else:
            pval = "[name({player_dbref})] fails to draw anything.".format(
                player_dbref=player_dbref)
        mux_commands.pemit(protocol, invoker_dbref, pval)


class UnitListCommand(BaseCommand):
    """
    Lists the units that the player owns.
    """

    command_name = "inv_units"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        class_choices = ['light', 'medium', 'heavy', 'assault']
        type_choices = ['mech', 'tank', 'vtol', 'battlesuit']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="units", description='Lists the units that you own.')

        parser.add_argument(
            "--class", type=str, choices=class_choices, dest='filter_class',
            help="Mech weight class to filter by")

        parser.add_argument(
            "--type", type=str, choices=type_choices, dest='filter_type',
            help="Unit type to filter by")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        lib_summary = yield get_player_unit_summary_list(invoker_dbref,
            filter_class=args.filter_class, filter_type=args.filter_type)
        pval = self._get_header_str('Unit Inventory Listing : %d results' % len(lib_summary['refs']))
        pval += '%r%b%b'
        for counter, udict in enumerate(lib_summary['refs'], start=1):
            weight = udict['weight']
            class_color = get_weight_class_color_for_tonnage(weight)
            pval += "[ljust({class_color}{reference}{ansi_normal}, 18)]".format(
                class_color=class_color,
                reference=udict['reference'],
                ansi_normal=ANSI_NORMAL,
            )
            if counter % 4 == 0:
                pval += "%r%b%b"
        if not lib_summary['refs']:
            pval += "[center(You don't own any units. Hit the arenas!,78)]"
        pval += self._get_footer_str(pad_char='-')
        pval += '%r[space(5)]'
        pval += '[ljust(%ch%cgLight,20)]'
        pval += '[ljust(%ch%cyMedium, 20)]'
        pval += '[ljust(%ch%crHeavy, 20)]'
        pval += '%ch%cmAssault'
        pval += '%r[space(22)]%cnFor more info, type %ch%units -h'
        pval += self._get_footer_str()
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class InventoryListCommand(BaseCommand):
    """
    Shows the main inventory list.
    """

    command_name = "inv_inventory"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cbill_balance = yield get_player_cbill_balance(invoker_dbref)
        # Have to escape the comma.
        cbill_str = "{:,}".format(cbill_balance).replace(',', '%,')
        inv_width = 50

        pval = self._get_header_str('Inventory', width=inv_width)
        pval += (
            "%r[center(%chCurrent C-Bill balance:%cn {cbill_balance},{inv_width})]".format(
                cbill_balance=cbill_str, inv_width=inv_width))
        pval += self._get_footer_str(pad_char='-', width=inv_width)
        pval += (
            "%r[center(To see your list of parts and weapons%, type:,{inv_width})]"
            "%r[center(%ch%cgitems%cn,{inv_width})]"
            "%r"
            "%r[center(To see your list of unit blueprints%, type:,{inv_width})]"
            "%r[center(%ch%cgblueprints%cn,{inv_width})]"
            "%r"
            "%r[center(To see your list of owned units%, type:,{inv_width})]"
            "%r[center(%ch%cgunits%cn,{inv_width})]"
            "".format(
                inv_width=inv_width))
        pval += self._get_footer_str(width=inv_width)
        mux_commands.pemit(protocol, [invoker_dbref], pval)


class InventoriesCommandTable(InboundCommandTable):

    commands = [
        ModItemInventoryCommand,
        ModBlueprintInventoryCommand,
        ModCbillsCommand,
        RewardBpCommand,

        InventoryListCommand,
        ItemsCommand,
        BlueprintsCommand,
        UnitListCommand,
    ]
