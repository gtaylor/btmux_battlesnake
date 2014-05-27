from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.unit_spawning.inbound_commands import \
    UnitSpawningCommandTable


class UnitSpawningPlugin(BattlesnakePlugin):
    """
    This plugin provides a convenient way to spawn units on maps.
    """

    command_tables = [UnitSpawningCommandTable]
