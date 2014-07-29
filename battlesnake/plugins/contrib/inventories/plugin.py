from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.inventories.inbound_commands import \
    InventoriesCommandTable


class InventoriesPlugin(BattlesnakePlugin):
    """
    Player inventory management.
    """

    command_tables = [InventoriesCommandTable]
