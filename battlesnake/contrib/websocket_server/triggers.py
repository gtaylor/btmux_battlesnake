import re

from battlesnake.contrib.hudinfo_cache.store import UNIT_STORE
from battlesnake.core.triggers import TriggerTable, Trigger


class UnitDestroyedTrigger(Trigger):
    """
    Triggered when a unit is destroyed.
    """

    # Thunderbolt [LA] has been destroyed by Generator [GA]!
    line_regex = re.compile(
        r'^(?P<victim_mech_name>.*) \[(?P<victim_id>[A-Za-z]{2})\] has been destroyed by (?P<killer_mech_name>.*) \[(?P<killer_id>[A-Za-z]{2})\]!\r$'
    )

    def run(self, protocol, line, re_match):
        """
        :param basestring line: The line that matched the trigger.
        :param re.MatchObject re_match: A Python MatchObject for the regex
            groups specified in the Trigger's regex string.
        """

        victim_id = re_match.group('victim_id').upper()
        killer_id = re_match.group('killer_id').upper()
        UNIT_STORE.mark_unit_as_destroyed_by_id(victim_id, killer_id)


class WebSocketServerTriggerTable(TriggerTable):
    """
    Triggers for the websocket server contrib.
    """

    triggers = [
        UnitDestroyedTrigger,
    ]
