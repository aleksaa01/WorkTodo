import os
import json
from utils.singletons import GenericSingleton
from api.dispatcher import ApiCallDispatcher
from api.resources import CardResource, TaskResource, PreferenceResource
from queue import Queue
from PyQt5.QtWidgets import QApplication


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

        self.cards = None
        self.tasks = None
        self.preferences = None
        self.token = None
        with open(self.path, 'r') as f:
            self.load_from_file(f)

        # Check saved attribute to see if file content and storage object are synchronized.
        self.saved = True
        # If debug is True, calling save() won't save anything.
        self.debug = False

        self.output_queue = Queue()
        self.dispatcher = ApiCallDispatcher(self.output_queue)
        if self.token:
            self.dispatcher.token = token

    def load_from_file(self, f):
        data = json.load(f)
        self.cards = [CardResource.from_json(resource) for resource in data['cards']]
        self.tasks = [TaskResource.from_json(resource) for resource in data['tasks']]
        self.preferences = [PreferenceResource.from_json(resource) for resource in data['preferences']]
        self.token = data['token']

    def is_authenticated(self):
        if self.token is None:
            return False
        assert isinstance(self.token, str), 'Token should be represented by string, got {} instead'.format(type(self.token))
        return True

    def authenticate(self, username, password):
        self.dispatcher.authenticate(0, username, password)

        while True:
            QApplication.processEvents()
            if self.output_queue.empty():
                continue
            job_id, future = self.output_queue.get()
            if job_id != 0:
                self.output_queue.put((job_id, future))
                continue

            token = future.result()
            self.dispatcher.token = token
            self.token = token
            break
        return True

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
    
    def update_preference(self, card_name, preference, new_value):
        self._preferences[card_name][preference] = new_value
        self.saved = False

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            cards_resource = [card.to_json() for card in self.cards]
            tasks_resource = [task.to_json() for task in self.tasks]
            preferences_resource = [pref.to_json() for pref in self.preferences]
            data = {'cards': cards_resource, 'tasks': tasks_resource, 'preferences': preferences_resource}
            json.dump(data, f)
        self.saved = True
        print("Storage state saved!")
