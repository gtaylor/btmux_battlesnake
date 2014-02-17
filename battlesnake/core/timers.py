"""
Timers are things that happen indefinitely on a pre-determined schedule.
"""

from txscheduling.cron import CronSchedule
from txscheduling.task import ScheduledCall
from twisted.internet.task import LoopingCall


class TimerTable(object):
    """
    The telnet protocol instance instantiates one of these to manage all
    timer. We handle timer activation via this class.
    """

    # A list of Timer sub-classes to register.
    timers = []

    def __init__(self, protocol):
        self.protocol = protocol
        # A list of time deferreds.
        self._timers = []
        # Get em' all registered at instantiation time.
        for timer in self.timers:
            self.register_timer(timer)

    def register_timer(self, timer_class):
        """
        Registers an existing Timer.

        :param Timer timer_class:
        """

        if issubclass(timer_class, IntervalTimer):
            self._register_interval_timer(timer_class)
        else:
            self._register_crontab_timer(timer_class)
        timer_class.on_register(self.protocol)

    def _register_interval_timer(self, timer_class):
        """
        Registers an IntervalTimer sub-class. These fire on intervals
        measured in seconds.
        """

        lc = LoopingCall(timer_class.fire, self.protocol)
        lc.start(timer_class.interval)

    def _register_crontab_timer(self, timer_class):
        """
        Registers a CrontabTimer sub-class. These fire on pre-set schedules.
        """

        schedule = CronSchedule(timer_class.schedule)
        # noinspection PyProtectedMember
        call = ScheduledCall(timer_class.fire, self.protocol)
        call.start(schedule)
        self._timers.append(call)


class BaseTimer(object):
    """
    Encapsulates everything needed to execute a recurring task. Don't
    sub-class this class directly. Choose one of the sub-classes below.
    """

    # Set this to True on your sub-class if the given timer should not
    # run when the bot is disconnected. Note that these timers are often
    # registered and running before the bot can connect, resulting in
    # transport == None errors if you try to issue a MUX outbound command.
    pause_when_bot_is_disconnected = False

    @classmethod
    def on_register(cls, protocol):
        """
        This is called when the timer is registered.
        """

        pass

    @classmethod
    def fire(cls, protocol):
        """
        To allow for instance variables to be used on the sub-classes,
        we instantiate the timer every time it is fired. This gives us a clean
        slate to work with each time.
        """

        if cls.pause_when_bot_is_disconnected and protocol.transport is None:
            return
        t = cls()
        t.run(protocol)

    def run(self, protocol):
        """
        This is called when the Timer is fired.

        :param BattlesnakeTelnetProtocol protocol: A reference back to the
            top level telnet protocol instance.
        """

        raise NotImplementedError("Override this method on your sub-class.")


class CronTimer(BaseTimer):
    """
    A UNIX cron-style timer. These fire at pre-determined times. The smallest
    possible interval for these is 60 seconds. If you need a tighter loop
    and don't need to schedule on specific minutes/hours/days, use the
    IntervalTimer class.
    """

    # A cron-style schedule string.
    schedule = None


class IntervalTimer(BaseTimer):
    """
    These timers fire every X seconds.

    .. note:: All interval timers are fired immediately upon bot startup.
    """

    # An interval int in seconds.
    interval = None
