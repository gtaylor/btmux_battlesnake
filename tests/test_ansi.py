import unittest

from battlesnake.core.ansi import remove_ansi_codes


class ANSITests(unittest.TestCase):

    def test_remove_escape_sequences(self):
        """
        Tests an command with no args included.
        """

        cleaned = remove_ansi_codes("%cr%chHello")
        self.assertEqual(len(cleaned), 5)
