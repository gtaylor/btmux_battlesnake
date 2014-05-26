import unittest

from battlesnake.core.utils import remove_all_percent_sequences


class UtilsTests(unittest.TestCase):

    def test_remove_all_percent_sequences(self):
        """
        Tests an command with no args included.
        """

        cleaned = remove_all_percent_sequences("%crHello%bThere%(%[")
        self.assertEqual(cleaned, "Hello There([")
