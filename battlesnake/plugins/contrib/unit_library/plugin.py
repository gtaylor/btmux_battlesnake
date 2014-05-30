from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.unit_library.inbound_commands import \
    UnitLibraryCommandTable


class UnitLibraryPlugin(BattlesnakePlugin):
    """
    A plugin for tracking unit specifics in the DB from in-game.
    """

    command_tables = [UnitLibraryCommandTable]
