import os
import json
from utils.singletons import GenericSingleton
from api.dispatcher import ApiCallDispatcher
from api.resources import CardResource, TaskResource, PreferenceResource
from queue import Queue
from PyQt5.QtWidgets import QApplication


STORAGE_NAME = "storage.json"


def unsave(func):
    def wrapper(instance, *args, **kwargs):
        return_value = func(instance, *args, **kwargs)
        instance.saved = False
        return return_value
    return wrapper


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
        self.cards = [CardResource.from_json(res) for res in data['cards']]
        self.tasks = [TaskResource.from_json(res) for res in data['tasks']]
        self.preferences = [PreferenceResource.from_json(res) for res in data['preferences']]
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

    def tasks_from_card(self, card_id):
        return [task for task in self.tasks if task.card_id == card_id]

    @unsave
    def add_card(self, card_resource):
        self.cards.append(card_resource)

    @unsave
    def add_task(self, task_resource):
        self.tasks.append(task_resource)
        cid = task_resource.card_id
        card = None
        for c in self.cards:
            if c.id == cid:
                c.tasks.append(task_resource.id)
                return
        assert False, 'Failed to add task. There is no card with id {}'.format(cid)

    @unsave
    def remove_card(self, card_id):
        index = self.cards.find(card_id)
        self.cards.pop(index)
        for idx, task in enumerate(self.tasks[:]):
            if task.card_id == card_id:
                self.tasks.pop(idx)
        for idx, pref in enumerate(self.preferences[:]):
            if pref.card_id == card_id:
                self.preferences.pop(idx)

    @unsave
    def pop_task(self, task_index):
        return self.tasks.pop(task_index)

    @unsave
    def insert_task(self, task_resource):
        self.tasks.insert(task_resource.position, task_resource)

    @unsave
    def update_task(self, task_resource):
        self.tasks[task_resource.position] = task_resource

    @unsave
    def update_preference(self, preference, card_id):
        for idx, pref in enumerate(self.preferences):
            if pref.card_id == card_id:
                self.preferences[idx] = preference
        assert False, "Preference with card_id {} doesn't exist".format(card_id)

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            cards_resource = [card.to_json() for card in self.cards]
            tasks_resource = [task.to_json() for task in self.tasks]
            preferences_resource = [pref.to_json() for pref in self.preferences]
            data = {
                'cards': cards_resource, 'tasks': tasks_resource,
                'preferences': preferences_resource, 'token': self.token
            }
            json.dump(data, f)
        self.saved = True
        print("Storage state saved!")
