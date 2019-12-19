from storage import Storage
from api.resources import CardResource
from tasks.models import TasksModel


#TODO: Synchronize CardsModel with the API.


class CardsModel(object):

    def __init__(self, storage):
        self._st = storage
        self._last_rid = None
        self._on_click_observers = []
        self._on_remove_observers = []

    def on_click(self, observer):
        self._on_click_observers.append(observer)

    def on_remove(self, observer):
        self._on_remove_observers.append(observer)

    def notify_show(self, card_rid):
        for observer in self._on_click_observers:
            observer(card_rid)

    def notify_remove(self, card_rid):
        for observer in self._on_remove_observers:
            observer(card_rid)

    def cards(self):
        return [(card.rid, card.name) for card in self._st.cards]

    def get_name(self, card_rid):
        return self._st.get_card(card_rid).name

    def add_card(self, card_name):
        new_rid = self._get_new_rid()
        card = CardResource(rid=new_rid, name=card_name)
        self._storage.add_card(card)

    def remove_card(self, card_rid):
        self._storage.remove_card(card_rid)
        self.notify_remove(card_rid)

    def show_card(self, card_rid):
        self.notify_show(card_rid)

    def update_card(self, card_rid, new_card_name):
        self._cards_map[card_rid].name = new_card_name
        self._storage.update_card(self._cards_map[card_rid])

    def _get_new_rid(self):
        new_rid = self._last_rid + 1 if self._last_rid else 1
        while True:
            if self._st.cards.get(new_rid, False):
                new_rid += 1
            else:
                return new_rid

    def get_task_model(self, card_rid):
        return TasksModel(self._st, card_rid)

    def get_card_preferences(self, card_rid):
        return PreferencesModel(self._st, card_rid)


class PreferencesModel(object):

    def __init__(self, storage, card_rid):
        self._st = storage
        self.crid = card_rid
        self.pref = storage.get_preference(card_rid)

    @property
    def show_date(self):
        return self.pref.show_date

    @show_date.setter
    def show_date(self, show):
        if isinstance(show, bool):
            self.pref.show_date = show
        else:
            raise TypeError('Need bool, got {} instead'.format(type(show)))

    @property
    def warning_time(self):
        return self.pref.warning_time

    @warning_time.setter
    def warning_time(self, time):
        if isinstance(time, int):
            self.pref.warning_time = time
        else:
            raise TypeError('Need int, got {} instead'.format(type(time)))

    @property
    def danger_time(self):
        return self.pref.danger_time

    @danger_time.setter
    def danger_time(self, time):
        if isinstance(time, int):
            self.pref.danger_time = time
        else:
            raise TypeError('Need int, got {} instead'.format(type(time)))
