from storage import Storage

class Rules(object):

    def __init__(self, card_name):
        self._storage = Storage()
        self.card_name = card_name
        self.rules = self._storage.rules(card_name)

    def update(self, new_rules):
        # add_rules is actually faster than update_rules
        # because it doesn't have to check if rules exist.
        self._storage.add_rules(self.card_name, new_rules)
        self.rules = new_rules

    def get(self, key, default):
        if self.rules:
            return self.rules[key]
        return default

    def __getitem__(self, item):
        return self.rules[item]

    def isset(self):
        return True if self.rules else False
