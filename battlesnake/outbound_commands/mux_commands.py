"""
Outbound command wrappers for base MUX commands.
"""
from battlesnake.core.utils import generate_unique_token


def set_attr(protocol, obj, name, value):
    """
    Wrapper for @set, in the context of an attribute.

    :param BattlesnakeTelnetProtocol protocol:
    :param string obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param string name: The attribute name.
    :param string value: The attribute value.
    """

    protocol.write("@set %s=%s:%s" % (obj, name, value))


def pemit(protocol, targets, message, switches=None, replace_returns=True):
    """
    Wrapper for @pemit. Handles multiple targets gracefully.

    :param BattlesnakeTelnetProtocol protocol:
    :param targets: A list of objects or a single object string.
    :param string message: The message to send.
    :keyword set switches: A set of switches to send.
    :keyword bool replace_returns: If ``True``, replace all carriage returns
        with the MUX %r return.
    """

    if replace_returns:
        message = message.replace('\r', '%r')

    if not switches:
        switches = set([])
    # We always use list mode, out of laziness.
    switches.add('list')
    if not isinstance(targets, list):
        targets = [targets]

    target_str = ' '.join(targets)
    switch_str = '/' + '/'.join(list(switches))
    protocol.write("@pemit%s %s=%s" % (switch_str, target_str, message))


def idle(protocol):
    """
    Used to run the IDLE command, which is a way to avoid timeouts due to
    poorly configured NATs.

    :param BattlesnakeTelnetProtocol protocol:
    """

    protocol.write("IDLE")


def think(protocol, thought, monitor_output=True):
    """
    Runs the 'think' command, which is useful for performing actions or
    retrieving values from the MUX. By setting a dynamic prefix, we can
    make sure that our response monitors pick up the output for the command
    we are waiting on.

    :param BattlesnakeTelnetProtocol protocol:
    :param basestring thought: The string to pass into the 'think' command.
    :keyword bool monitor_output: If ``True``, this function returns a Deferred
        that will be called when the response of this 'think' invocation
        comes back. If ``False``, this function returns nothing. It's slightly
        more efficient to set this to False if you don't need to see
        the output.
    :rtype: None or defer.Deferred
    :returns: A Deferred if ``monitor_output`` is ``True``, ``None`` if not.
    """

    prefix = generate_unique_token()
    command_str = 'think %s%s' % (prefix, thought)
    if monitor_output:
        regex_str = r'^' + prefix + '(?P<value>.*)\r$'
        result = protocol.expect(regex_str, return_regex_group='value')
    protocol.write(command_str)
    if monitor_output:
        # noinspection PyUnboundLocalVariable
        return result
