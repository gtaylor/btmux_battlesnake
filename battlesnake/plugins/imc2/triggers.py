import re

from battlesnake.core.triggers import TriggerTable
from battlesnake.core.triggers import Trigger
from battlesnake.plugins.imc2 import imc2
from battlesnake.plugins.imc2.channel_map import MUX_TO_IMC2_CHANNEL_MAP


class ChannelMessageTrigger(Trigger):
    """
    Tries to identify potential IMC2 channel activity.
    """

    line_regex = re.compile(r'.*\[(?P<channel>.*)\] (?P<author>[\w`$_\-.,\']+)[:] (?P<message>.*)\r')

    def run(self, protocol, line, re_match):
        """
        :param basestring line: The line that matched the trigger.
        :param re.MatchObject re_match: A Python MatchObject for the regex
            groups specified in the Trigger's regex string.
        """

        channel = re_match.group("channel")
        author = re_match.group("author")
        message = re_match.group("message")

        imc2_channel = MUX_TO_IMC2_CHANNEL_MAP.get(channel, None)
        imc2.IMC2_PROTO_INSTANCE.data_out(
            text=message, packet_type="broadcast", sender=author,
            channel=imc2_channel)


class IMC2TriggerTable(TriggerTable):

    triggers = [
        ChannelMessageTrigger,
    ]
