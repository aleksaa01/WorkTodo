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


class Preferences(object):

    def __init__(self, card_name):
        self._storage = Storage()
        self.card_name = card_name

        self._expiration = None
        self._show_date = None

        self._load()

    def _load(self, preferences):
        for item, value in self._storage.preferences(self.card_name):
            if getattr(self, item, '\0') == '\0':
                raise AttributeError("Unkown preference attribute: {}".format(item))
            else:
                setattr(self, item, value)

    @property
    def expiration(self):
        return self._expiration

    @expiration.setter
    def expiration(self, value):
        if not isinstance(value, dict):
            return TypeError("expiration value must be of type dict, "
                             "got {} instead.".format(type(value)))
        self._expiration = value

    @property
    def show_date(self):
        return self._show_date

    @show_date.setter
    def show_date(self, value):
        if not isinstance(value, bool):
            return TypeError("show_date value must be of type bool, "
                             "got {} instead.".format(type(value)))
        self._show_date = value
