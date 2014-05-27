import re

from battlesnake.plugins.contrib.hudinfo_cache.store import UNIT_STORE, HudinfoCParser
from battlesnake.core.triggers import TriggerTable, Trigger


class HudinfoContactsTrigger(Trigger):
    """
    Triggered by a HUDINFO C (contacts) line. Stuffs the parsed data into
    the hudinfo_cache store.
    """

    line_regex = re.compile(
        r'#HUD:(?P<hudinfo_key>.*):C:L# (?P<contact_data>.*)\r$'
    )

    def run(self, protocol, line, re_match):
        """
        :param basestring line: The line that matched the trigger.
        :param re.MatchObject re_match: A Python MatchObject for the regex
            groups specified in the Trigger's regex string.
        """

        contact_data = re_match.group('contact_data')
        unit = HudinfoCParser().parse(contact_data)
        UNIT_STORE.update_or_add_unit(unit)


class HudinfoCacheTriggerTable(TriggerTable):
    """
    Triggers for the hudinfo_cache contrib.
    """

    triggers = [
        HudinfoContactsTrigger,
    ]
