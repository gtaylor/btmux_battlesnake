from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.imc2.triggers import IMC2TriggerTable


class IMC2Plugin(BattlesnakePlugin):
    """
    This plugin maps local channels to remote IMC2 channels.
    """

    trigger_tables = [IMC2TriggerTable]
