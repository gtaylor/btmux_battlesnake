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


class ResponseWatcherManager(object):
    """
    The higher level client protocol instantiates one of these to manage
    all response watchers. We handle registration, matching, and expiration
    through this object.
    """

    def __init__(self):
        self.watcher_store = {}
        self.expiration_loop = LoopingCall(self.expire_stale_watchers)

    def watch(self, regex_str, timeout_secs, return_regex_group):
        """
        Creates and registers a watcher in one shot.

        :param basestring regex_str: A regular expression string to match against.
        :param float timeout_secs: How many seconds to wait.
        :rtype: defer.Deferred
        """

        mon = ResponseWatcher(regex_str, timeout_secs, return_regex_group)
        self.register_watcher(mon)
        return mon.deferred

    def register_watcher(self, watcher):
        """
        Registers an existing ResponseWatcher.

        :param ResponseWatcher watcher: The watcher to register.
        """

        tdelt = datetime.timedelta(seconds=watcher.timeout_secs)
        watcher.timeout = datetime.datetime.now() + tdelt
        self.watcher_store[watcher.id] = watcher

    def match_line(self, line):
        """
        Given a line read by the upstream protocol, see if it matches any
        of the watchers. If so, we issue a callback on the deferred and
        return ``True``.

        :param basestring line: The line read by the protocol.
        :rtype: re.MatchObject or None
        :returns: A MatchObject if ther was a match, or None if not.
        """

        for watcher_id, watcher in self.watcher_store.items():
            match = watcher.line_regex.search(line)
            if not match:
                continue
            # At this point, we can assume there was a match.
            if watcher.return_regex_group:
                watcher.deferred.callback(match.group(watcher.return_regex_group))
            else:
                watcher.deferred.callback(match)
            del self.watcher_store[watcher_id]
            return True
        return False

    def start_expiration_loop(self):
        """
        Fires up the expiration loop.
        """

        loop_interval = float(settings.get('bot', 'response_watcher_expire_check_interval'))
        print "* Response watcher expiration loop interval: %ss" % loop_interval
        self.expiration_loop.start(loop_interval)

    def expire_stale_watchers(self):
        """
        Goes through the list of watchers and errbacks any that haven't
        been matched in their allotted time window.
        """

        now = datetime.datetime.now()
        for watcher_id, watcher in self.watcher_store.items():
            if watcher.deferred.called:
                del self.watcher_store[watcher_id]
                continue
            if now >= watcher.timeout:
                watcher.deferred.errback(NoResponseMatchFoundError())
                del self.watcher_store[watcher_id]


class ResponseWatcher(object):
    """
    Encapsulates everything we need to wait for an expected output.
    """

    def __init__(self, regex_str, timeout_secs, return_regex_group):
        self.id = uuid.uuid4().hex
        self.timeout_secs = timeout_secs
        # This gets populated when this watcher is registered with the manager.
        self.timeout = None
        self.deferred = defer.Deferred()
        self.line_regex = re.compile(regex_str)
        self.return_regex_group = return_regex_group


class NoResponseMatchFoundError(Exception):
    """
    Raised when no match for expected output is found within the timeout window.
    """

    def __init__(self, *args):
        Exception.__init__(self, "No response watch match found.", *args)
