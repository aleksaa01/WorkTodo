import os
import json
from utils.singletons import GenericSingleton


STORAGE_NAME = 'storage.json'


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

        self._storage = None
        with open(self.path, 'r') as f:
            self._storage = json.load(f)

        # Check saved attribute to see if file content and storage object are synchronized.
        self.saved = True
        # If debug is True, calling save() won't save anything.
        self.debug = False

    def cards(self):
        return list(self._storage.keys())

    def tasks(self, card_name):
        return self._storage[card_name]

    def task_names(self, card_name):
        tasks = self.tasks(card_name)
        task_names = [''] * len(tasks)
        for index, task in enumerate(tasks):
            task_names[index] = task['name']

        return task_names

    def add_card(self, card_name):
        self._storage[card_name] = []
        self.saved = False

    def add_task(self, card_name, task):
        if not isinstance(task, dict):
            raise TypeError('Task value must be of type dict, got {} instead.'.format(type(task)))

        self._storage[card_name].append(task)
        self.saved = False

    def remove_card(self, card_name):
        self._storage.pop(card_name)
        self.saved = False

    def pop_task(self, card_name, task_index):
        self.saved = False
        return self._storage[card_name].pop(task_index)

    def insert_task(self, card_name, task, index):
        self._storage[card_name].insert(index, task)
        self.saved = False

    def get_task(self, card_name, task_name):
        for task in self._storage[card_name]:
            if task['name'] == task_name:
                return task

    def update_task_at(self, card_name, index, new_task):
        self._storage[card_name][index] = new_task
        print('Task at index {} has been updated.'.format(index))

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            json.dump(self._storage, f)
        self.saved = True
        print('Storage state saved!')
