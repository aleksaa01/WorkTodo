from PyQt5.QtCore import QObject
from tasks.objects import TaskObject, create_task_object
from storage import Storage


class TasksModel(QObject):

    def __init__(self, todo_name):
        self.name = todo_name
        self._storage = Storage()
        self._tasks = None
        self._load_tasks()

    def _load_tasks(self):
        self._tasks = [TaskObject(raw_task) for raw_task in self._storage.tasks(self.name)]

    def tasks(self):
        return self._tasks

    def get_task(self, index):
        return self._tasks[index]

    def insert_task(self, index, task_object):
        return self._tasks.insert(index, task_object)

    def pop_task(self, index):
        return self._tasks.pop(index)

    def find_task(self, text):
        for idx, task in enumerate(self._tasks):
            if task.description == text:
                return idx
        return -1
