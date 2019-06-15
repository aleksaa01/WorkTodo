from PyQt5.QtCore import QObject
from ..tasks.objects import TaskObject, create_task_object
from ..storage import Storage


class TasksModel(QObject):

    def __init__(self, todo_name):
        self.name = todo_name
        self._storage = Storage()
        self._load_tasks()

    def _load_tasks(self):
        self._tasks = [TaskObject(raw_task) for raw_task in self._storage.tasks(self.name)]
