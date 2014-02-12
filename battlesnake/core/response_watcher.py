"""
This module gives us a way to wait for output from the MUX that matches a
certain pattern. For example, it would allow us to do something like run a
command in-game to return the list of connected players.
"""

import re
import uuid
import datetime

from twisted.internet import defer
from twisted.internet.task import LoopingCall

from battlesnake.conf import settings


class ResponseMonitorManager(object):
    """
    The higher level client protocol instantiates one of these to manage
    all response monitors. We handle registration, matching, and expiration
    through this object.
    """

    def __init__(self):
        self.monitor_store = {}
        self.expiration_loop = LoopingCall(self.expire_stale_monitors)

    def monitor(self, regex_str, timeout_secs, return_regex_group):
        """
        Creates and registers a monitor in one shot.

        :param basestring regex_str: A regular expression string to match against.
        :param float timeout_secs: How many seconds to wait.
        :rtype: defer.Deferred
        """

        mon = ResponseMonitor(regex_str, timeout_secs, return_regex_group)
        self.register_monitor(mon)
        return mon.deferred

    def register_monitor(self, monitor):
        """
        Registers an existing ResponseMonitor.

        :param ResponseMonitor monitor: The monitor to register.
        """

        tdelt = datetime.timedelta(seconds=monitor.timeout_secs)
        monitor.timeout = datetime.datetime.now() + tdelt
        self.monitor_store[monitor.id] = monitor

    def match_line(self, line):
        """
        Given a line read by the upstream protocol, see if it matches any
        of the monitors. If so, we issue a callback on the deferred and
        return ``True``.

        :param basestring line: The line read by the protocol.
        :rtype: re.MatchObject or None
        :returns: A MatchObject if ther was a match, or None if not.
        """

        for monitor_id, monitor in self.monitor_store.items():
            match = monitor.line_regex.search(line)
            if not match:
                continue
            # At this point, we can assume there was a match.
            if monitor.return_regex_group:
                monitor.deferred.callback(match.group(monitor.return_regex_group))
            else:
                monitor.deferred.callback(match)
            del self.monitor_store[monitor_id]
            return True
        return False

    def start_expiration_loop(self):
        """
        Fires up the expiration loop.
        """

        loop_interval = float(settings.get('bot', 'monitor_expire_check_interval'))
        print "* Monitor expiration loop interval: %ss" % loop_interval
        self.expiration_loop.start(loop_interval)

    def expire_stale_monitors(self):
        """
        Goes through the list of monitors and errbacks any that haven't
        been matched in their allotted time window.
        """

        now = datetime.datetime.now()
        for monitor_id, monitor in self.monitor_store.items():
            if monitor.deferred.called:
                del self.monitor_store[monitor_id]
                continue
            if now >= monitor.timeout:
                monitor.deferred.errback(NoResponseMatchFoundError())
                del self.monitor_store[monitor_id]


class ResponseMonitor(object):
    """
    Encapsulates everything we need to wait for an expected output.
    """

    def __init__(self, regex_str, timeout_secs, return_regex_group):
        self.id = uuid.uuid4().hex
        self.timeout_secs = timeout_secs
        # This gets populated when this monitor is registered with the manager.
        self.timeout = None
        self.deferred = defer.Deferred()
        self.line_regex = re.compile(regex_str)
        self.return_regex_group = return_regex_group


class NoResponseMatchFoundError(Exception):
    """
    Raised when no match for expected output is found within the timeout window.
    """

    def __init__(self, *args):
        Exception.__init__(self, "No response match found.", *args)
