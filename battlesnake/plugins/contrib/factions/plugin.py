from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.factions.inbound_commands import FactionCommandTable


class FactionPlugin(BattlesnakePlugin):
    """
    Example plugin to use as a starting point.
    """

    command_tables = [FactionCommandTable]
