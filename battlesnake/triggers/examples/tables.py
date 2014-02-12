from battlesnake.core.triggers import TriggerTable
from battlesnake.triggers.examples import triggers


class ExampleTriggerTable(TriggerTable):
    """
    Some example triggers for you to play with.
    """

    triggers = [
        triggers.SayHelloTrigger,
    ]