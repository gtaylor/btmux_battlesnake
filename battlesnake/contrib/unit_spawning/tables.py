from battlesnake.core.inbound_command_handling.command_table import InboundCommandTable

from battlesnake.contrib.unit_spawning import commands as spawning_commands


class UnitSpawningCommandTable(InboundCommandTable):

    commands = [
        spawning_commands.SpawnUnitCommand,
    ]
