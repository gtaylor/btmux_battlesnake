from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.example_plugin.inbound_commands import ExampleCommandTable
from battlesnake.plugins.example_plugin.triggers import ExampleTriggerTable


class ExamplePlugin(BattlesnakePlugin):
    """
    Example plugin to use as a starting point.
    """

    trigger_tables = [ExampleTriggerTable]
    command_tables = [ExampleCommandTable]
