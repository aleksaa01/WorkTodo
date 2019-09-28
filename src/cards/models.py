from storage import Storage
from api.resources import CardResource


class CardModel(object):

    def __init__(self):
        self._storage = Storage()
        self._cards = self._storage.cards()

    def cards(self):
        return self._cards

    def add_card(self, card_name):
        self._cards.append(card_name)
        self._storage.add_card(card_name)

    def remove_card(self, card_name):
        self._cards.remove(card_name)
        self._storage.remove_card(card_name)


class CardsModel(object):

    def __init__(self, storage):
        self._storage = storage
        self._cards_map = {card.id: card for card in storage.cards()}

    def cards(self):
        return self._cards_map.values()

    def task_ids(self, card_id):
        return self._cards_map[card_id]

    def preference_ids(self, card_id):
        return self._cards_map[card_id]

    def add_card(self, card_name):
        new_id = self._get_new_id()
        card = CardResource(id=new_id, name=card_name)
        self._cards_map[new_id] = card
        self._storage.add_card(card)

    def add_task_id(self, card_id, task_id):
        self._cards_map[card_id].tasks.append(task_id)

    def add_preference_id(self, card_id, preference_id):
        self._cards_map[card_id].preferences.append(preference_id)

    def remove_task_id(self, card_id, task_id):
        self._cards_map[card_id].tasks.remove(task_id)

    def remove_preference_id(self, card_id, preference_id):
        self._cards_map[card_id].preferences.remove(preference_id)

    def remove_card(self, card_id):
        self._cards_map.pop(card_id)
        self._storage.remove_card(card_id)

    def update_card(self, card_id, new_card_name):
        self._cards_map[card_id].name = new_card_name
        self._storage.update_card(self._cards_map[card_id])

    def _get_new_id(self):
        new_id = 1
        while True:
            if self._cards_map.get(new_id, False):
                new_id += 1
            else:
                return new_id
