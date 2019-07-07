import os
import json
from utils.singletons import GenericSingleton


STORAGE_NAME = "storage.json"


class Storage(object, metaclass=GenericSingleton):

    def __init__(self, filename=None, path=None):
        self.name = filename if filename else STORAGE_NAME
        if path:
            if path.endswith(filename):
                self.path = path
            else:
                self.path = os.path.join(path, filename)
        else:
            self.path = os.path.join(os.getcwd(), self.name)

        with open(self.path, 'r') as f:
            storage = json.load(f)

        self._cards = storage["data"]
        self._preferences = storage["preferences"]

        # Check saved attribute to see if file content and storage object are synchronized.
        self.saved = True
        # If debug is True, calling save() won't save anything.
        self.debug = False

    def cards(self):
        return list(self._cards.keys())

    def tasks(self, card_name):
        return self._cards[card_name]["tasks"]

    def preferences(self, card_name):
        return self._preferences[card_name]

    def task_names(self, card_name):
        tasks = self.tasks(card_name)
        task_names = [''] * len(tasks)
        for index, task in enumerate(tasks):
            task_names[index] = task["name"]

        return task_names

    def add_card(self, card_name):
        self._cards[card_name] = {"tasks": []}
        self._preferences[card_name] = {"rules": {}}
        self.saved = False

    def add_task(self, card_name, task):
        if not isinstance(task, dict):
            raise TypeError("Task value must be of type dict, got {} instead.".format(type(task)))

        self._cards[card_name]["tasks"].append(task)
        self.saved = False

    def remove_card(self, card_name):
        self._cards.pop(card_name)
        self._preferences.pop(card_name)
        self.saved = False

    def pop_task(self, card_name, task_index):
        self.saved = False
        return self._cards[card_name]["tasks"].pop(task_index)

    def insert_task(self, card_name, task, index):
        self._cards[card_name]["tasks"].insert(index, task)
        self.saved = False

    def get_task(self, card_name, task_name):
        for task in self._cards[card_name]["tasks"]:
            if task["name"] == task_name:
                return task

    def update_task_at(self, card_name, index, new_task):
        self._cards[card_name]["tasks"][index] = new_task
        print("Task at index {} has been updated.".format(index))
        self.saved = False
    
    def add_rules(self, card_name, rules):
        if not isinstance(rules, dict):
            raise TypeError("Rules value must be of type dict, got {} instead.".format(type(rules)))

        self._preferences[card_name]["rules"] = rules
        self.saved = False

    def update_rules(self, card_name, rules):
        if not isinstance(rules, dict):
            raise TypeError("Rules value must be of type dict, got {} instead.".format(type(rules)))

        rules = self._preferences[card_name].get("rules")
        # Checks if rules is either None or {}
        if not rules:
            raise KeyError("Card {}, doesn't have rules.".format(card_name))

        self._preferences[card_name]["rules"] = rules
        self.saved = False

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            storage = {"cards": self._cards, "preferences": self._preferences}
            json.dump(storage, f)
        self.saved = True
        print("Storage state saved!")
