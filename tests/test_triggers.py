import unittest

from battlesnake.core.triggers import TriggerTable, Trigger


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.trigger_table = TriggerTable()

    def test_say_hello(self):
        """
        Tests a trigger on the 'say' command and a specific value.
        """

        trigger = Trigger(r'(?P<talker>.*) says "[Hh]ello"', lambda s: s)
        self.trigger_table.register_trigger(trigger)
        # This should poop out a tuple in the form of trigger, re.MatchObject.
        _, match = self.trigger_table.match_line('Some Guy says "hello"')
        self.assertEqual(match.group('talker'), 'Some Guy')