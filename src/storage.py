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
        return self._storage[queue_name]

    def add_queue(self, queue_name):
        self._storage[queue_name] = []
        self.saved = False

    def add_task(self, queue_name, task_name, value):
        if not isinstance(value, dict):
            raise TypeError('Task value must be of type dict, got {} instead.'.format(type(value)))

        self._storage[queue_name].append([task_name, value])
        self.saved = False

    def remove_queue(self, queue_name):
        self._storage.pop(queue_name)
        self.saved = False

    def remove_task(self, queue_name, task_name):
        index = self._find_task(queue_name, task_name)
        self._storage.pop(index)
        self.saved = False

    def move_task_up(self, queue_name, task_name, moves=1):
        task_index = self._find_task(queue_name, task_name)
        temp_tasks = self._storage[queue_name]
        task = temp_tasks[task_index]

        end_index = max(0, task_index - moves)
        for i in range(task_index, end_index, -1):
            temp_tasks[i] = temp_tasks[i - 1]

        temp_tasks[end_index] = task
        self._storage[queue_name] = temp_tasks
        self.saved = False

    def move_task_down(self, queue_name, task_name, moves=1):
        task_index = self._find_task(queue_name, task_name)
        temp_tasks = self._storage[queue_name]
        task = temp_tasks[task_index]

        end_index = min(len(temp_tasks) - 1, task_index + moves)
        for i in range(task_index, end_index):
            temp_tasks[i] = temp_tasks[i + 1]

        temp_tasks[end_index] = task
        self._storage[queue_name] = temp_tasks
        self.saved = False

    def _find_task(self, queue_name, task_name):
        for index, field in enumerate(self._storage[queue_name]):
            if task_name == field[0]:
                return index
        raise ValueError("Task with name: {}, doesn't exist.")


    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._storage, f)
        self.saved = True
