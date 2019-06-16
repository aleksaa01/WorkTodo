from PyQt5.QtCore import QObject
from tasks.objects import TaskObject, create_task_object
from storage import Storage


class TodoModel(QObject):

    def __init__(self):
        self._storage = Storage()
        self._todos = self._storage.todos()

    def todos(self):
        return self._todos
