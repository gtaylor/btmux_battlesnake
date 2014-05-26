

class Faction(object):
    """
    This class represents an in-game Faction.
    """

    def __init__(self, dbref, name):
        self.dbref = dbref
        self.name = name

    @property
    def team_num(self):
        return self.dbref[1:]
