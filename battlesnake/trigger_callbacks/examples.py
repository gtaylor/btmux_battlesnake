from battlesnake.outbound_commands import mux_commands


# noinspection PyUnusedLocal
def say_hello_callback(protocol, line, re_match):
    """
    Responds to a player saying "hello" in the same room as the bot.

    :param basestring line: The line that matched the trigger.
    :param re.MatchObject re_match: A Python MatchObject for the regex
        groups specified in the Trigger's regex string.
    """

    talkers_name = re_match.group("talker")
    response = "Why hello there, {talkers_name}.".format(talkers_name=talkers_name)
    mux_commands.say(protocol, response)