from storage import Storage

class Rules(object):

    def __init__(self, card_name):
        self._storage = Storage()
        self.rules = self._storage.rules(card_name)

    def update_rules(self, new_rules):
        # add_rules is actually faster than update_rules
        # because it doesn't have to check if rules exist.
        self._storage.add_rules(new_rules)

    def __getitem__(self, item):
        return self.rules[item]

    def isset(self):
        return True if self.rules else False
