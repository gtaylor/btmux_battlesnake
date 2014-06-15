from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.chargen.inbound_commands import ChargenCommandTable


class ChargenPlugin(BattlesnakePlugin):
    """
    Character generation/setup. Set skills, character attributes, other
    boring stuff.
    """

    command_tables = [ChargenCommandTable]
