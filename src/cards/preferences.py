from storage import Storage


class Preferences(object):

    def __init__(self, card_name):
        self._storage = Storage()
        self.card_name = card_name

        self._expiration = None
        self._show_date = None

        # self.loaded is a workaround for avoiding changing the storage
        # when loading preferences from it. This happens because we are
        # dynamically setting the instance variables which also have to be checked.
        self.loaded = False
        self._load()
        self.loaded = True

    def _load(self):
        for item, value in self._storage.preferences(self.card_name).items():
            if getattr(self, item, '\0') == '\0':
                raise AttributeError("Unkown preference attribute: {}".format(item))
            else:
                setattr(self, item, value)

    def _update_preference(self, name, value):
        if not self.loaded:
            return
        self._storage.update_preference(self.card_name, name, value)

    @property
    def expiration(self):
        return self._expiration

    @expiration.setter
    def expiration(self, value):
        if not isinstance(value, dict):
            return TypeError("expiration value must be of type dict, "
                             "got {} instead.".format(type(value)))
        self._expiration = value
        self._update_preference("expiration", value)

    @property
    def show_date(self):
        return self._show_date

    @show_date.setter
    def show_date(self, value):
        if not isinstance(value, bool):
            return TypeError("show_date value must be of type bool, "
                             "got {} instead.".format(type(value)))
        self._show_date = value
        self._update_preference("show_date", value)
