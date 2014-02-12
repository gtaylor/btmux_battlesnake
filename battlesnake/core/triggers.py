"""
Triggers are somewhat like response watchers, only they never expire and
they can be matched and fired repeatedly. They also don't use deferreds,
and instead run the callback function directly.
"""


class TriggerTable(object):
    """
    The telnet protocol instance instantiates one of these to manage all
    triggers. We handle trigger registration and matching through this class.
    """

    # A list of Trigger sub-classes to register.
    triggers = []

    def __init__(self):
        self._triggers = []
        # Get em' all registered at instantiation time.
        for trigger in self.triggers:
            self.register_trigger(trigger)

    def register_trigger(self, trigger):
        """
        Registers an existing Trigger.

        :param Trigger trigger:
        """

        self._triggers.append(trigger)

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

        for trigger in self._triggers:
            match = trigger.line_regex.search(line)
            if not match:
                continue
            return trigger, match


class Trigger(object):
    """
    Encapsulates everything needed to match a line of output to a particular
    regex string. Sub-class this for each trigger.
    """

    # This must be set to a compiled regexp in your sub-class.
    line_regex = None

    def run(self, protocol, line, re_match):
        """
        This is called when the trigger is matched and fired.

        :param BattlesnakeTelnetProtocol protocol: A reference back to the
            top level telnet protocol instance.
        :param basestring line: The line that set the trigger off.
        :param re.MatchObject re_match: The Python regexp match object.
        """

        raise NotImplementedError("Override this method on your sub-class.")
