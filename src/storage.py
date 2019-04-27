import os
import sqlite3
import json


STORAGE_NAME = 'storage.json'


class QueueStorage(object):

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

    def queues(self):
        return list(self._storage.keys())

    def tasks(self, queue_name):
        return list(self._storage[queue_name].keys())

    def add_queue(self, queue_name):
        self._storage[queue_name] = {}
        self.saved = False

    def add_task(self, queue_name, task_name, value):
        if not isinstance(value, dict):
            raise TypeError('Task value must be of type dict, got {} instead.'.format(type(value)))

        self._storage[queue_name][task_name] = value
        self.saved = False

    def remove_queue(self, queue_name):
        self._storage.pop(queue_name)
        self.saved = False

    def remove_task(self, queue_name, task_name):
        self._storage[queue_name].pop(task_name)
        self.saved = False

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._storage, f)
        self.saved = True
