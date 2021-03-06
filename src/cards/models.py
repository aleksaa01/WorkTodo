from storage import Storage
from api.resources import CardResource, PreferenceResource
from tasks.models import TasksModel


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
        num_cards = len(self._st.cards)
        card = CardResource(rid=new_rid, name=card_name, position=num_cards)
        self._st.add_card(card)
        pref_rid = self._get_new_pref_rid()
        pref = PreferenceResource(rid=pref_rid, card_rid=new_rid, warning_time=0,
                                  danger_time=0, show_date=False)
        self._st.add_preference(new_rid, pref)
        return new_rid

    def remove_card(self, card_rid):
        self._st.remove_card(card_rid)
        self.notify_remove(card_rid)

    def show_card(self, card_rid):
        self.notify_show(card_rid)

    def update_card(self, card_rid, new_card_name):
        self._cards_map[card_rid].name = new_card_name
        self._storage.update_card(self._cards_map[card_rid])

    def _get_new_rid(self):
        new_rid = self._last_rid + 1 if self._last_rid else 1
        while True:
            if new_rid in self._st.card_rids:
                new_rid += 1
            else:
                return new_rid

    def _get_new_pref_rid(self):
        new_rid = 0
        while True:
            if new_rid in self._st.preference_rids:
                new_rid += 1
            else:
                return new_rid

    def get_task_model(self, card_rid):
        return TasksModel(self._st, card_rid)

    def get_card_preferences(self, card_rid):
        return PreferencesModel(self._st, card_rid)

    def transfer_task(self, from_crid, to_crid, from_idx, to_idx):
        task = self._st.pop_task(from_crid, from_idx)
        task.card_rid = to_crid
        self._st.insert_task(to_crid, to_idx, task)


class PreferencesModel(object):

    def __init__(self, storage, card_rid):
        self._st = storage
        self.crid = card_rid

    @property
    def show_date(self):
        return self._st.get_preference_field(self.crid, 'show_date')

    @show_date.setter
    def show_date(self, show):
        if isinstance(show, bool):
            self._st.update_preference(self.crid, 'show_date', show)
        else:
            raise TypeError('Need bool, got {} instead'.format(type(show)))

    @property
    def warning_time(self):
        return self._st.get_preference_field(self.crid, 'warning_time')

    @warning_time.setter
    def warning_time(self, time):
        if isinstance(time, int):
            self._st.update_preference(self.crid, 'warning_time', time)
        else:
            raise TypeError('Need int, got {} instead'.format(type(time)))

    @property
    def danger_time(self):
        return self._st.get_preference_field(self.crid, 'danger_time')

    @danger_time.setter
    def danger_time(self, time):
        if isinstance(time, int):
            self._st.update_preference(self.crid, 'danger_time', time)
        else:
            raise TypeError('Need int, got {} instead'.format(type(time)))
