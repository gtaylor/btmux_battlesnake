from battlesnake.core.inbound_command_handling.command_table import InboundCommandTable
from battlesnake.inbound_commands.bot_management import commands as bot_commands


class BotManagementCommandTable(InboundCommandTable):
    """
    Command table for bot management commands.
    """

    commands = [
        bot_commands.BotInfoCommand,
        bot_commands.BotWaitTestCommand,
    ]
