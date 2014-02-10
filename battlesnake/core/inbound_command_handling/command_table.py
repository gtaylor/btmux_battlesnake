

class InboundCommandTable(object):
    """
    Handles inbound command lookups and registration.
    """

    def __init__(self):
        # The keys are trigger strings, the values are BaseCommand sub-classes.
        self.commands = {}

    def register_command(self, command):
        """
        :param command: A BaseCommand sub-class to register.
        """

        assert command.trigger_str not in self.commands, \
            "Trigger str already registered: %s" % command.trigger_str

        self.commands[command.trigger_str] = command

    def match_inbound_command(self, parsed_command_line):
        """
        Given a ParsedInboundCommandLine, look up the trigger string in
        the table and return the matching BaseCommand sub-class.

        :param ParsedInboundCommandLine parsed_command_line: The parsed
            command. We're only interested in the trigger string in this case.
        :rtype: BaseCommand or None
        :returns: Either a matching BaseCommand sub-class if there's a match,
            or None if there isn't.
        """

        return self.commands.get(parsed_command_line.trigger_str, None)
