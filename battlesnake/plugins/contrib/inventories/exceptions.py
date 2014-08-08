
class InsufficientItemInventory(Exception):

    def __init__(self, missing_dict):
        self.missing_dict = missing_dict
        super(InsufficientItemInventory, self).__init__(missing_dict)

    def __str__(self):
        return u"Missing items: %s" % self.missing_dict


class InsufficientBlueprintInventory(Exception):

    def __init__(self, missing_dict):
        self.missing_dict = missing_dict
        super(InsufficientBlueprintInventory, self).__init__(missing_dict)

    def __str__(self):
        return u"Missing blueprints: %s" % self.missing_dict


class InsufficientCbills(Exception):
    pass
