

class InboundCommandTable(object):
    """
    Handles inbound command lookups and registration. Sub-class this and
    modify the ``commands`` class attribute to contain your BaseCommand
    sub-classes.
    """

    # A list of BaseCommand sub-classes to register.
    commands = []

    def __init__(self):
        # The keys are command names, the values are BaseCommand sub-classes.
        self._command_dict = {}
        # Get em' all registered at instantiation time.
        for command in self.commands:
            self.register_command(command)

    def register_command(self, command):
        """
        :param command: A BaseCommand sub-class to register.
        """

        assert command.command_name not in self._command_dict, \
            "Inbound command name already registered: %s" % command.command_name

        self._command_dict[command.command_name] = command

    def match_inbound_command(self, parsed_command_line):
        """
        Given a ParsedInboundCommandLine, look up the command name in
        the table and return the matching BaseCommand sub-class.

        :param ParsedInboundCommandLine parsed_command_line: The parsed
            command. We're only interested in the command name in this case.
        :rtype: BaseCommand or None
        :returns: Either a matching BaseCommand sub-class if there's a match,
            or None if there isn't.
        """

        return self._command_dict.get(parsed_command_line.command_name, None)
