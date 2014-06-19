from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.player_profiles.inbound_commands import \
    PlayerProfilesCommandTable


class PlayerProfilesPlugin(BattlesnakePlugin):
    """
    This plugin allows for managing player profiles, accounts, and some
    basic info on each.
    """

    command_tables = [PlayerProfilesCommandTable]
