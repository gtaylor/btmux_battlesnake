"""
Outbound command wrappers for base MUX commands.
"""

from battlesnake.core.utils import generate_unique_token


def set_attr(protocol, obj, attr, val):
    """
    Wrapper for @set, in the context of an attribute.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str attr: The attribute name.
    :param str val: The attribute value.
    """

    command_str = "@set {obj}={attr}:{val}".format(
        obj=obj, attr=attr, val=val)
    u_attr = attr.upper()
    ack_regex = r'{u_attr} - Set.\r$'.format(u_attr=u_attr)
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def startup(protocol, obj, startup_val):
    """
    Wrapper for @startup.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str startup_val: Value for the object's Startup attribute.
    """

    startup_str = "@startup {obj}={startup_val}".format(
        obj=obj, startup_val=startup_val)
    ack_regex = r'Startup - Set.\r$'
    return protocol.write_and_wait(startup_str, ack_regex_str=ack_regex)


def parent(protocol, obj, parent_obj):
    """
    Wrapper for @parent.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str parent_obj: A MUX object string for the parent to set.
    """

    parent_str = "@parent {obj}={parent_obj}".format(
        obj=obj, parent_obj=parent_obj)
    ack_regex = r'Parent set.\r$'
    return protocol.write_and_wait(parent_str, ack_regex_str=ack_regex)


def say(protocol, message):
    """
    Wrapper for say.
    """

    protocol.write("say " + message)


def pemit(protocol, targets, message, switches=None, replace_returns=True):
    """
    Wrapper for @pemit. Handles multiple targets gracefully.

    :param BattlesnakeTelnetProtocol protocol:
    :param targets: A list of objects or a single object string.
    :param str message: The message to send.
    :keyword set switches: A set of switches to send.
    :keyword bool replace_returns: If ``True``, replace all carriage returns
        with the MUX %r return.
    """

    if replace_returns:
        message = message.replace('\r', '%r')
        message = message.replace('\n', '%r')

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


def think(protocol, thought, return_output=True):
    """
    Runs the 'think' command, which is useful for performing actions or
    retrieving values from the MUX. By setting a dynamic prefix, we can
    make sure that our response monitors pick up the output for the command
    we are waiting on.

    :param BattlesnakeTelnetProtocol protocol:
    :param str thought: The string to pass into the 'think' command.
    :keyword bool return_output: If ``True``, this function returns a Deferred
        that will be called when the response of this 'think' invocation
        comes back. If ``False``, this function returns nothing. It's slightly
        more efficient to set this to False if you don't need to see
        the output.
    :rtype: None or defer.Deferred
    :returns: A Deferred if ``return_output`` is ``True``, ``None`` if not.
    """

    prefix = generate_unique_token()
    command_str = 'think %s%s' % (prefix, thought)
    if return_output:
        regex_str = r'^' + prefix + '(?P<value>.*)\r$'
        deferred = protocol.expect(regex_str, return_regex_group='value')
    protocol.write(command_str)
    if return_output:
        # noinspection PyUnboundLocalVariable
        return deferred


def lock(protocol, obj, lockval, whichlock=None):
    """
    Wrapper for @lock in the object (not attribute) form.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str lockval: The attribute name to lock to. You can also add the
        expected value here with a slash and the value as normal.
    :type whichlock: str or None
    :param whichlock: One of the lock types: use, enter, leave. If not specified,
        the default lock is assumed.
    """

    if whichlock:
        whichlock_switch = '/' + whichlock
    else:
        whichlock_switch = ''
    command_str = "@lock{whichlock_switch} {obj}={lockval}".format(
        whichlock_switch=whichlock_switch, obj=obj, lockval=lockval)
    ack_regex = r'Locked.\r$'
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def link(protocol, obj, target_obj):
    """
    Links an object to the target.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str target_obj: A MUX object string for the target to link to.
    """

    command_str = "@link {obj}={target_obj}".format(
        obj=obj, target_obj=target_obj)
    ack_regex = r'Home set.\r$'
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def force(protocol, obj, force_command):
    """
    Forces an object to do something.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str force_command: The command to force the object to do.
    """

    command_str = "@force {obj}={force_command}".format(
        obj=obj, force_command=force_command)
    return protocol.write_and_wait(command_str)


def name(protocol, obj, new_name):
    """
    Re-names an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str new_name: The object's new name.
    """

    command_str = "@name {obj}={new_name}".format(
        obj=obj, new_name=new_name)
    ack_regex = r'Name set.\r$'
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def drain(protocol, obj):
    """
    Runs @drain on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    """

    command_str = "@drain {obj}".format(obj=obj)
    ack_regex = r'Drained.\r$'
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def notify(protocol, obj):
    """
    Runs @notify on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    """

    command_str = "@notify {obj}".format(obj=obj)
    ack_regex = r'Notified.\r$'
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)


def trigger(protocol, obj, attr, params=None):
    """
    Runs @trigger on an object.

    :param BattlesnakeTelnetProtocol protocol:
    :param str obj: A valid MUX object string. 'me', 'here', a dbref, etc.
    :param str attr: The attribute to trigger.
    :type params: list or None
    :param params: A list of param strings to pass to the trigger attribute.
    """

    param_str = ""
    if params:
        param_str = "=" + ','.join(params)
    command_str = "@trigger {obj}/{attr}{param_str}".format(
        obj=obj, attr=attr, param_str=param_str)
    u_attr = attr.upper()
    ack_regex = r'{u_attr} - Triggered.\r$'.format(u_attr=u_attr)
    return protocol.write_and_wait(command_str, ack_regex_str=ack_regex)
