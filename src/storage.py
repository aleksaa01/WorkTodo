import os
import sqlite3
import json


STORAGE_NAME = 'storage.json'


class TodoStorage(object):

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

    def todos(self):
        return list(self._storage.keys())

    def tasks(self, todo_name):
        return self._storage[todo_name]

    def task_names(self, todo_name):
        tasks = self.tasks(todo_name)
        task_names = [''] * len(tasks)
        for index, task in enumerate(tasks):
            task_names[index] = task['name']

        return task_names

    def add_todo(self, todo_name):
        self._storage[todo_name] = []
        self.saved = False

    def add_task(self, todo_name, task):
        if not isinstance(task, dict):
            raise TypeError('Task value must be of type dict, got {} instead.'.format(type(task)))

        self._storage[todo_name].append(task)
        self.saved = False

    def remove_todo(self, todo_name):
        self._storage.pop(todo_name)
        self.saved = False

    def remove_task(self, todo_name, task_name):
        index = self.find_task(todo_name, task_name)
        self._storage[todo_name].pop(index)
        self.saved = False

    def remove_task_by_index(self, todo_name, task_index):
        self._storage[todo_name].pop(task_index)
        self.saved = False

    def move_task_up_by_name(self, todo_name, task_name, moves=1):
        task_index = self.find_task(todo_name, task_name)
        end_index = task_name - moves
        self._move_task_up(todo_name, task_index, end_index)

    def move_task_down_by_name(self, todo_name, task_name, moves=1):
        task_index = self.find_task(todo_name, task_name)
        end_index = task_index + moves
        self._move_task_down(todo_name, task_index, end_index)

    def move_task_by_index(self, todo_name, task_index, end_index):
        print('Moving task with index {} to index {}'.format(task_index, end_index))

        if task_index <= end_index:
            self._move_task_down(todo_name, task_index, end_index)
        else:
            self._move_task_up(todo_name, task_index, end_index)

        print(self.tasks(todo_name))

    def _move_task_up(self, todo_name, task_index, end_index):
        temp_tasks = self._storage[todo_name]
        task = temp_tasks[task_index]
        # check if end_index is out of range, and if it is set it to beginning of the list
        end_index = max(0, end_index)
        for i in range(task_index, end_index, -1):
            temp_tasks[i] = temp_tasks[i - 1]

        temp_tasks[end_index] = task
        self._storage[todo_name] = temp_tasks

        self.saved = False

    def _move_task_down(self, todo_name, task_index, end_index):
        temp_tasks = self._storage[todo_name]
        task = temp_tasks[task_index]
        # check if end_index is out of range, and if it is set it to end of the list
        end_index = min(len(temp_tasks) - 1, end_index)
        for i in range(task_index, end_index):
            temp_tasks[i] = temp_tasks[i + 1]

        temp_tasks[end_index] = task
        self._storage[todo_name] = temp_tasks

        self.saved = False

    def find_task(self, todo_name, task_name):
        for index, field in enumerate(self._storage[todo_name]):
            if task_name == field['name']:
                return index
        raise ValueError("Task with name: {}, doesn't exist.".format(task_name))

    def pop_task(self, todo_name, task_index):
        self.saved = False
        return self._storage[todo_name].pop(task_index)

    def insert_task(self, todo_name, task, index):
        self._storage[todo_name].insert(index, task)
        self.saved = False

    def get_task(self, todo_name, task_name):
        for task in self._storage[todo_name]:
            if task['name'] == task_name:
                return task

    def update_task(self, todo_name, old_task, new_task):
        old_task_index = self.find_task(todo_name, old_task)
        self._storage[todo_name][old_task_index] = new_task
        print('Task at index {} has been updated.'.format(old_task_index))

    def update_task_at(self, todo_name, index, new_task):
        self._storage[todo_name][index] = new_task
        print('Task at index {} has been updated.'.format(index))

    def save(self):
        if self.debug:
            return
        with open(self.path, 'w') as f:
            json.dump(self._storage, f)
        self.saved = True
        print('Storage state saved!')
