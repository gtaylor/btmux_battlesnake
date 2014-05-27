

class BattlesnakePlugin(object):
    """
    All Battlesnake plugins should inherit from this class. You generally
    shouldn't need to override it.
    """

    trigger_tables = []
    timer_tables = []
    command_tables = []

    def __init__(self):
        self.protocol = None

    def post_connect_setup(self, protocol):
        """
        Handles loading the plugin once the telnet protocol has succesfully
        connected and authenticated.

        :param BattlesnakeTelnetProtocol protocol: The telnet protocol instance.
        :rtype: tuple
        :returns: A tuple in the form of (trigger_tables, timer_tables,
            command_tables). The telnet protocol loads these up for consideration
            before entering the 'monitoring' state.
        """

        self.protocol = protocol
        trigger_tables = []
        timer_tables = []
        command_tables = []

        for trigger_table in self.trigger_tables:
            trigger_tables.append(trigger_table())
        for timer_table in self.timer_tables:
            timer_tables.append(timer_table(protocol))
        for command_table in self.command_tables:
            command_tables.append(command_table())
        return trigger_tables, timer_tables, command_tables
