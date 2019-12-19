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
            self.dispatcher.token = self.token

    @unsave
    def fetch_cards(self):
        jid = 1
        self.dispatcher.get_cards(jid)
        future = self.extract_future(jid)

        self.cards = future.result()
        print('Cards updated.')

    @unsave
    def fetch_tasks(self):
        self.tasks = {}
        jid = 2
        self.dispatcher.get_tasks(jid)
        future = self.extract_future(jid)

        for task in future.result():
            if self.tasks.get(task.card_rid, None) is None:
                self.tasks[task.card_rid] = []
            task_pos = task.position
            curr_len = len(self.tasks[task.card_rid])
            if curr_len <= task_pos:
                self.tasks[task.card_rid].extend([0] * (task_pos - curr_len))
            self.tasks[task.card_rid].insert(task_pos, task)
        print('Taks updated.')

    @unsave
    def fetch_preferences(self):
        self.preferences = {}
        jid = 3
        self.dispatcher.get_preferences(jid)
        future = self.extract_future(jid)

        for pref in future.result():
            self.preferences[pref.card_rid] = pref

    def fetch_all(self):
        self.fetch_cards()
        self.fetch_tasks()
        self.fetch_preferences()


    def extract_future(self, jid):
        while True:
            QApplication.processEvents()
            if self.output_queue.empty():
                continue
            job_id, future = self.output_queue.get()
            if job_id != jid:
                self.output_queue.put((job_id, future))
                continue
            return future


    def load_from_file(self, f):
        data = json.load(f)
        self.cards = [CardResource.from_json(res) for res in data['cards']]
        self._tasks = {card.rid: [] for card in self.cards}
        for task in data['tasks']:
            self.tasks[task.card_rid].append(task)
        # Added for prevention of continuous rid number growth(check fast if rid exists and reuse deleted)
        self.task_rids = set()
        self.preferences = {}
        for resource in data['preferences']:
            pref = PreferenceResource.from_json(resource)
            self.preferences[pref.card_rid] = pref
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

    def register(self, callback, email, username, password):
        jid = 5
        self.dispatcher.register(jid, email, username, password)

        while True:
            QApplication.processEvents()
            if self.output_queue.empty():
                continue
            job_id, future = self.output_queue.get()
            if job_id != jid:
                self.output_queue.put((job_id, future))
                continue

            result = future.result()
            status_code, message = result
            is_valid = True if status_code == 201 else False
            callback(is_valid, message)

    def get_preference(self, card_rid):
        return self.preferences[card_rid]

    def get_card(self, card_rid):
        for c in self.cards:
            if c.rid == card_rid:
                return c
        raise ValueError("Card with rid {} doesn't exist.".format(card_rid))

    def get_task(self, card_rid, task_idx):
        return self.tasks[card_rid][task_idx]

    def find_task(self, card_rid, task_rid):
        for t in self.tasks[card_rid]:
            if t.rid == task_rid:
                return t
        raise ValueError("Task with rid {} doesn't exist".format(task_rid))

    def tasks(self, card_rid):
        return self._tasks[card_rid]

    @unsave
    def add_card(self, card_resource):
        self.cards.append(card_resource)
        self.tasks[card_resource.rid] = []

    @unsave
    def add_task(self, card_rid, task_resource):
        self.tasks[card_rid].append(task_resource)
        self.task_rids.add(task_resource.rid)
        crid = task_resource.card_rid
        card = None
        for c in self.cards:
            if c.rid == crid:
                c.tasks.append(task_resource.rid)
                return
        raise ValueError('Failed to add task. There is no card with rid {}'.format(cid))

    @unsave
    def remove_card(self, card_rid):
        index = -1
        for idx, c in enumerate(self.cards):
            if c.rid == card_rid:
                index = idx
                break
        assert index != -1, "Can't remove card, card with rid {} doesn't exist."

        self.cards.pop(index)
        tasks = self.tasks.pop(card_rid)
        for task in tasks:
            self.task_rids.remove(task.rid)
        self.preferences.pop(card_rid)

    @unsave
    def pop_task(self, card_rid, task_index):
        task = self.tasks[card_rid].pop(task_index)
        self.task_rids.remove(task.rid)
        return task

    @unsave
    def insert_task(self, card_rid, idx, task_resource):
        self.tasks[card_rid].insert(idx, task_resource)
        self.task_rids.add(task_resource.rid)

    @unsave
    def move_task(self, card_rid, old_idx, new_idx):
        task_list = self.tasks[card_rid]
        task = task_list[old_idx]
        for idx in range(old_idx, new_idx):
            task_list[idx] = task_list[idx + 1]
        task_list[idx + 1] = task

    @unsave
    def update_task(self, card_rid, idx, task_resource):
        self.tasks[card_rid][idx] = task_resource

    @unsave
    def update_preference(self, card_rid, preference):
        self.preferences[card_rid] = preference

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            cards_resource = [card.to_json() for card in self.cards]
            tasks_resource = []
            for task_list in self._tasks.values():
                tasks_resource.extend(task_list)
            preferences_resource = [pref.to_json() for pref in self.preferences.values()]
            data = {
                'cards': cards_resource, 'tasks': tasks_resource,
                'preferences': preferences_resource, 'token': self.token
            }
            json.dump(data, f)
        self.saved = True
        print("Storage state saved!")
