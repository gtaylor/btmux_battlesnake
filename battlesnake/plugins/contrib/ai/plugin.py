from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.ai.inbound_commands import AICommandTable


class AiPlugin(BattlesnakePlugin):
    """
    This plugin provides some basic AI management commands.
    """

    command_tables = [AICommandTable]
