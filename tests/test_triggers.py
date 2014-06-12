import unittest

from battlesnake.plugins.example_plugin.triggers import ExampleTriggerTable


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.trigger_table = ExampleTriggerTable()

    def test_say_hello(self):
        """
        Tests a trigger on the 'say' command and a specific value.
        """

        _, match = self.trigger_table.match_line('Some Guy says "hello"')
        self.assertEqual(match.group('talker'), 'Some Guy')
