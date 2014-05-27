

class ArenaMasterPuppetStore(object):
    """
    This class is responsible for tracking arena puppets, which serve as the
    eyes and areas of the bot.
    """

    def __init__(self):
        self._puppet_store = {}

    def update_or_add_puppet(self, puppet):

        self._puppet_store[puppet.dbref] = puppet


class ArenaMasterPuppet(object):
    """
    Represents a single puppet.
    """

    def __init__(self, dbref, map_dbref):
        self.dbref = dbref
        self.map_dbref = map_dbref


# Lame that we have to pollute the global namespace, but whatevs.
PUPPET_STORE = ArenaMasterPuppetStore()
