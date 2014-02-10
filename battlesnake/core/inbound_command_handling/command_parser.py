

class ParsedInboundCommandLine(object):
    """
    Contains a parsed command line, which can be passed off to the command
    table, and eventually an individual BaseCommand sub-class.
    """

    def __init__(self, trigger_str, invoker_dbref, **kwargs):
        self.trigger_str = trigger_str
        self.invoker_dbref = invoker_dbref
        self.kwargs = kwargs

    def __repr__(self):
        return "<Command: '%s' from %s, kwargs %s>" % (
            self.trigger_str, self.invoker_dbref, self.kwargs)


def parse_line(line, prefix_str, kwarg_delim, list_delim):
    """
    Parses a line received by the BattlesnakeTelnetProtocol instance driving
    our client. Spits out a ParsedCommand instance for the command handler
    to use.

    :param string line: The line to parse.
    :param string prefix_str: The set of characters that form the command
        prefix string. If a line starts with these, we know we are dealing
        with a command.
    :param string kwarg_delim: The delimiter that separates kwargs from one
        another in the line.
    :rtype: ParsedInboundCommandLine
    """

    if not line.startswith(prefix_str):
        return

    stripped_line = line.strip()
    # We already know the prefix is there, lop it off to get to the goodies.
    cmd_str = stripped_line[len(prefix_str):]
    # First half is the trigger string, second half is the invoker and kwargs.
    cmd_split = cmd_str.split(kwarg_delim, 1)
    if len(cmd_split) < 2:
        return None

    trigger_str = cmd_split[0]
    kwarg_str = cmd_split[1]
    # Break up the rest of the string into kwarg items.
    kwarg_split = kwarg_str.split(kwarg_delim)
    # Invoker is always the first arg in the kwarg string. It has no key, just
    # a value.
    invoker_dbref = kwarg_split[0]

    kwargs = {}
    # We start at index 1 to skip the invoker dbref.
    for kwarg_pair in kwarg_split[1:]:
        # Each item in this list should be a string with a key and a value,
        # separated by the kwarg_delim. If the value has the list_delim in it,
        # the value ends up being a list of items.
        if not kwarg_pair:
            # This pair has no key or value.
            continue

        # Split key and value apart.
        k_split = kwarg_pair.split('=', 1)
        if len(k_split) == 1:
            # Key with no value. This is invalid syntax, since it lacks
            # an equal sign, ie: "key". Discard.
            continue
        if k_split[0] == '':
            # This may have had a value, but no key. Can't do anything with it.
            # For example: "=val"
            continue

        # This item has a key and a value separated by the = character.
        # For example: "key=val"
        key, val = k_split

        # Now let's see if our value is a list.
        val_items = val.split(list_delim)
        if len(val_items) > 1:
            # Looks like we have at least one list delimeter.
            # Only accept non-empty items.
            val = [item for item in val_items if item != '']
        kwargs[key] = val

    return ParsedInboundCommandLine(trigger_str, invoker_dbref, **kwargs)
