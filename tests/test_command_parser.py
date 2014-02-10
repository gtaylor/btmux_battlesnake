import unittest

from battlesnake.core.inbound_command_handling.command_parser import parse_line


class ParseLineTests(unittest.TestCase):
    PREFIX_STR = "PREFIX"
    KWARG_DELIM = "KWARGD"
    LIST_DELIM = "LISTD"

    PARSE_KWARGS = {
        'prefix_str': PREFIX_STR,
        'kwarg_delim': KWARG_DELIM,
        'list_delim': LIST_DELIM
    }

    def test_parse_no_args(self):
        """
        Tests an command with no args included.
        """

        line = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}"
        parsed = parse_line(line.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        self.assertEqual(parsed.trigger_str, 'command')
        self.assertEqual(parsed.invoker_dbref, '#212')
        self.assertEqual(parsed.kwargs, {})

    def test_parse_with_kwargs(self):
        """
        Tests the parsing of kwargs.
        """

        line1 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key=val"
        # Add a trailing delimeter. Make sure it doesn't impact the values.
        line2 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key=val{kwarg_delim}"
        parsed1 = parse_line(line1.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        parsed2 = parse_line(line2.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        self.assertEqual(parsed1.trigger_str, 'command')
        self.assertEqual(parsed2.trigger_str, 'command')
        self.assertEqual(parsed1.invoker_dbref, '#212')
        self.assertEqual(parsed2.invoker_dbref, '#212')
        self.assertEqual(parsed1.kwargs, {'key': 'val'})
        self.assertEqual(parsed2.kwargs, {'key': 'val'})

    def test_parse_with_empty_value_kwarg(self):
        """
        Tests our ability to interpret empty string values.
        """

        line1 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key={kwarg_delim}"
        parsed1 = parse_line(line1.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        self.assertEqual(parsed1.trigger_str, 'command')
        self.assertEqual(parsed1.invoker_dbref, '#212')
        self.assertEqual(parsed1.kwargs, {'key': ''})

    def test_parse_with_invalid_kwargs(self):
        """
        Tests the parsing of kwargs when at least one is invalid.
        """

        # This JustAKey kwarg is only a key without a value. It should be
        # discarded.
        line1 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}JustAKey{kwarg_delim}key=val{kwarg_delim}"
        parsed1 = parse_line(line1.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        self.assertEqual(parsed1.trigger_str, 'command')
        self.assertEqual(parsed1.invoker_dbref, '#212')
        self.assertEqual(parsed1.kwargs, {'key': 'val'})

    def test_parse_kwarg_with_list(self):
        """
        Tests the parsing of kwarg items that have list values.
        """

        line1 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key=item1{list_delim}item2"
        # Add a list delim, but no value after it. The mere presence of a list
        # delim converts the value to a list, even if it only has one item.
        line2 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key=item1{list_delim}{kwarg_delim}"
        vals = {
            'prefix_str': self.PREFIX_STR,
            'kwarg_delim': self.KWARG_DELIM,
            'list_delim': self.LIST_DELIM
        }
        parsed1 = parse_line(line1.format(**vals), **self.PARSE_KWARGS)
        parsed2 = parse_line(line2.format(**vals), **self.PARSE_KWARGS)
        self.assertEqual(parsed1.trigger_str, 'command')
        self.assertEqual(parsed2.trigger_str, 'command')
        self.assertEqual(parsed1.invoker_dbref, '#212')
        self.assertEqual(parsed2.invoker_dbref, '#212')
        self.assertEqual(parsed1.kwargs, {'key': ['item1', 'item2']})
        self.assertEqual(parsed2.kwargs, {'key': ['item1']})

    def test_parse_kwarg_with_empty_list(self):
        """
        Tests the parsing of a kwarg with a list delim but no values.
        """

        line1 = "{prefix_str}command{kwarg_delim}#212{kwarg_delim}key={list_delim}"
        parsed1 = parse_line(line1.format(**self.PARSE_KWARGS), **self.PARSE_KWARGS)
        self.assertEqual(parsed1.trigger_str, 'command')
        self.assertEqual(parsed1.invoker_dbref, '#212')
        self.assertEqual(parsed1.kwargs, {'key': []})