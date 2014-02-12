"""
Triggers are somewhat like response watchers, only they never expire and
they can be matched and fired repeatedly. They also don't use deferreds,
and instead run the callback function directly.
"""

import re


class TriggerTable(object):
    """
    The telnet protocol instance instantiates one of these to manage all
    triggers. We handle trigger registration and matching through this class.
    """

    def __init__(self):
        self.triggers = []

    def register_trigger(self, trigger):
        """
        Registers an existing Trigger.

        :param Trigger trigger:
        """

        self.triggers.append(trigger)

    def match_line(self, line):
        """
        Given a line read by the upstream protocol, see if it matches any
        of the triggers. If so, return the trigger and the re.MatchGroup.

        :param basestring line: The line read by the protocol.
        :rtype: tuple or None
        :returns: If a match was found, return a tuple in the form of
            (Trigger instance, re.MatchGroup). If no match was found,
            return None instead.
        """

        for trigger in self.triggers:
            match = trigger.line_regex.search(line)
            if not match:
                continue
            return trigger, match


class Trigger(object):
    """
    Encapsulates everything needed to match a line of output to a particular
    regex string.
    """

    def __init__(self, re_str, callback_func):
        self.line_regex = re.compile(re_str)
        # This is the function that gets called when the trigger is matched.
        self.callback_func = callback_func