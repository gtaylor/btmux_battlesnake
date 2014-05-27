from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.nat_idler.timers import NatIdlerTimerTable


class NatIdlerPlugin(BattlesnakePlugin):
    """
    Example plugin to use as a starting point.
    """

    timer_tables = [NatIdlerTimerTable]
