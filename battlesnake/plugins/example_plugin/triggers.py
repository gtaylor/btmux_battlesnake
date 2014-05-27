import re

from battlesnake.core.triggers import TriggerTable
from battlesnake.core.triggers import Trigger
from battlesnake.outbound_commands import mux_commands


class SayHelloTrigger(Trigger):
    """
    Responds to a player saying "hello" in the same room as the bot.
    """

    line_regex = re.compile(r'(?P<talker>.*) says "[Hh]ello"')

    def run(self, protocol, line, re_match):
        """
        :param basestring line: The line that matched the trigger.
        :param re.MatchObject re_match: A Python MatchObject for the regex
            groups specified in the Trigger's regex string.
        """

        talkers_name = re_match.group("talker")
        response = "Why hello there, {talkers_name}.".format(talkers_name=talkers_name)
        mux_commands.say(protocol, response)


class ExampleTriggerTable(TriggerTable):
    """
    Some example triggers for you to play with.
    """

    triggers = [
        SayHelloTrigger,
    ]
