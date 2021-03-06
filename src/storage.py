import os
import json
from requests.exceptions import ConnectionError
from utils.singletons import GenericSingleton
from api.dispatcher import ApiCallDispatcher
from api.resources import CardResource, TaskResource, PreferenceResource
from queue import Queue
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from api.methods import NoInternetConnection, InvalidCredentials


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

        self.cards = []
        self.card_rids = set()
        self._tasks = {}
        self.task_rids = set()
        self.preferences = {}
        self.preference_rids = set()
        self.token = None
        # You have to load first, in order to check if token exists.
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
        jid = self.dispatcher.get_cards()
        future = self.extract_future(jid)

        self.cards = future.result()
        for c in self.cards:
            self.card_rids.add(c.rid)
            self._tasks[c.rid] = []
        print('Cards updated.')

    @unsave
    def fetch_tasks(self):
        jid = self.dispatcher.get_tasks()
        future = self.extract_future(jid)

        for task in future.result():
            task_pos = task.position
            curr_len = len(self._tasks[task.card_rid])
            if curr_len <= task_pos:
                self._tasks[task.card_rid].extend([0] * (1 + task_pos - curr_len))
            self._tasks[task.card_rid][task_pos] = task
            self.task_rids.add(task.rid)
        print('Taks updated.')

    @unsave
    def fetch_preferences(self):
        self.preferences = {}
        jid = self.dispatcher.get_preferences()
        future = self.extract_future(jid)

        for pref in future.result():
            self.preferences[pref.card_rid] = pref
            self.preference_rids.add(pref.rid)

    def fetch_all(self):
        self.fetch_cards()
        self.fetch_tasks()
        self.fetch_preferences()
        self.save()


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
        for task_data in data['tasks']:
            task_res = TaskResource.from_json(task_data)
            self._tasks[task_res.card_rid].append(task_res)
            self.task_rids.add(task_res.rid)
        self.preferences = {}
        for resource in data['preferences']:
            pref = PreferenceResource.from_json(resource)
            self.preferences[pref.card_rid] = pref
            self.preference_rids.add(pref.rid)
        self.token = data['token']

    def is_authenticated(self):
        if self.token is None:
            return False
        assert isinstance(self.token, str), 'Token should be represented by string, got {} instead'.format(type(self.token))
        return True

    def authenticate(self, username, password):
        jid = self.dispatcher.authenticate(username, password)

        future = self.extract_future(jid)
        try:
            token = future.result()
        except ConnectionError:
            return NoInternetConnection

        if isinstance(token, str):
            self.dispatcher.token = token
            self.token = token
        else:
            return InvalidCredentials
        return True

    def register(self, email, username, password):
        jid = self.dispatcher.register(email, username, password)

        future = self.extract_future(jid)
        try:
            reg_message = future.result()
        except ConnectionError:
            return NoInternetConnection

        if reg_message is True:
            return True
        else:
            return reg_message

    def get_preference(self, card_rid):
        return self.preferences[card_rid]

    def get_preference_field(self, card_rid, field):
        return getattr(self.preferences[card_rid], field)

    def get_card(self, card_rid):
        for c in self.cards:
            if c.rid == card_rid:
                return c
        raise ValueError("Card with rid {} doesn't exist.".format(card_rid))

    def get_task(self, card_rid, task_idx):
        return self._tasks[card_rid][task_idx]

    def find_task(self, card_rid, task_rid):
        for t in self._tasks[card_rid]:
            if t.rid == task_rid:
                return t
        raise ValueError("Task with rid {} doesn't exist".format(task_rid))

    def tasks(self, card_rid):
        return self._tasks[card_rid]

    @unsave
    def add_card(self, card_resource):
        self.cards.append(card_resource)
        self.card_rids.add(card_resource.rid)
        self._tasks[card_resource.rid] = []

    @unsave
    def add_task(self, card_rid, task_resource):
        self._tasks[card_rid].append(task_resource)
        self.task_rids.add(task_resource.rid)

    @unsave
    def add_preference(self, card_rid, preference_resource):
        if self.preferences.get(card_rid, False):
            raise ValueError("Can't add preference, card with rid={} "
                             "already has preference set.".format(card_rid))
        self.preferences[card_rid] = preference_resource
        self.preference_rids.add(preference_resource.rid)

    @unsave
    def remove_card(self, card_rid):
        index = -1
        for idx, card in enumerate(self.cards):
            if card.rid == card_rid:
                index = idx
                break
        assert index != -1, "Can't remove card, card with rid={} doesn't exist.".format(card_rid)

        self.cards.pop(index)
        self.card_rids.remove(card_rid)
        tasks = self._tasks.pop(card_rid)
        for task in tasks:
            self.task_rids.remove(task.rid)
        pref = self.preferences.pop(card_rid)
        self.preference_rids.remove(pref.rid)

    @unsave
    def pop_task(self, card_rid, task_index):
        task = self._tasks[card_rid].pop(task_index)
        self.task_rids.remove(task.rid)
        return task

    @unsave
    def insert_task(self, card_rid, idx, task_resource):
        self._tasks[card_rid].insert(idx, task_resource)
        self.task_rids.add(task_resource.rid)

    @unsave
    def move_task(self, card_rid, old_idx, new_idx):
        task_list = self._tasks[card_rid]
        task = task_list[old_idx]
        if old_idx < new_idx:
            for idx in range(old_idx, new_idx):
                task_list[idx] = task_list[idx + 1]
        else:
            for idx in range(old_idx, new_idx, -1):
                task_list[idx] = task_list[idx - 1]
        task_list[new_idx] = task

    @unsave
    def update_task(self, card_rid, idx, task_resource):
        self._tasks[card_rid][idx] = task_resource

    @unsave
    def update_preference(self, card_rid, field, new_value):
        # check if attribute exists first
        getattr(self.preferences[card_rid], field)
        setattr(self.preferences[card_rid], field, new_value)

    @unsave
    def replace_preference(self, card_rid, preference_resource):
        self.preferences[card_rid] = preference_resource

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            cards_resource = [card.to_json() for card in self.cards]
            tasks_resource = []
            for task_list in self._tasks.values():
                tasks_resource.extend([task.to_json() for task in task_list])
            preferences_resource = [pref.to_json() for pref in self.preferences.values()]
            data = {
                'cards': cards_resource, 'tasks': tasks_resource,
                'preferences': preferences_resource, 'token': self.token
            }
            json.dump(data, f)
        self.saved = True
        print("Storage state saved!")

    def sync(self):
        with open(self.path, 'r') as f:
            file_data = json.load(f)

        self._fix_positions(self.cards)
        for task_list in self._tasks.values():
            self._fix_positions(task_list)

        cards_resource = [card.to_json() for card in self.cards]
        tasks_resource = []
        for task_list in self._tasks.values():
            tasks_resource.extend([task.to_json() for task in task_list])
        preferences_resource = [pref.to_json() for pref in self.preferences.values()]

        data = {
            'cards': cards_resource, 'tasks': tasks_resource,
            'preferences': preferences_resource, 'token': self.token
        }
        jid = self.dispatcher.sync(file_data, data)
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self._check_for_sync_errors(jid))
        self.timer.start(1000)

    def _fix_positions(self, resource_list):
        for idx, res in enumerate(resource_list):
            res.position = idx

    def _check_for_sync_errors(self, jid):
        print('Checking for sync errors...')
        num_items = self.output_queue.qsize()
        for _ in range(num_items):
            job_id, future = self.output_queue.get()
            if job_id != jid:
                self.output_queue.put((job_id, future))
            else:
                try:
                    if not future.done():
                        self.output_queue.put((job_id, future))
                        return
                    res = future.result()
                except Exception as err:
                    print('Dispatcher error:', err)
                    self.timer.stop()
                    raise
                print('Dispatcher result:', res)
                self.timer.stop()
                return

    def wipe(self):
        data = {'cards': [], 'tasks': [], 'preferences': [], 'token': None}
        with open(self.path, 'w') as f:
            json.dump(data, f)
