from PyQt5.QtCore import QObject
from tasks.objects import TaskObject, create_task_object
from storage import Storage


class CardModel(QObject):

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
