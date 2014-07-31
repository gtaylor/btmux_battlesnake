
class InsufficientInventory(Exception):

    def __init__(self, missing_dict):
        self.missing_dict = missing_dict
        super(InsufficientInventory, self).__init__(missing_dict)

    def __str__(self):
        return u"Missing items: %s" % self.missing_dict
