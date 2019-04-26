import os
import sqlite3
import json


STORAGE_NAME = 'storage.json'


class JsonStorage(object):

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

    def tables(self):
        return list(self._storage.keys())

    def tasks(self, table_name):
        return list(self._storage[table_name].keys())

    def add_table(self, table_name):
        self._storage[table_name] = {}
        self.saved = False

    def add_task(self, table_name, task_name, value):
        if not isinstance(task, dict):
            raise TypeError('Task must be of type dict, got {} instead.'.format(type(task)))

        self._storage[table_name][task_name] = value
        self.saved = False

    def remove_table(self, table_name):
        self._storage.pop(table_name)
        self.saved = False

    def remove_task(self, table_name, task_name):
        self._storage[table_name].pop(task_name)
        self.saved = False

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._storage, f)
        self.saved = True
