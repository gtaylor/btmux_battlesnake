from battlesnake.core.timers import TimerTable
from battlesnake.timers.bot_misc import timers


class BotMiscTimerTable(TimerTable):
    """
    Misc. core bot timers.
    """

    timers = [
        timers.IdleTimer,
    ]
