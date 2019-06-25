from PyQt5.QtCore import QObject
from tasks.objects import TaskObject, create_task_object
from storage import Storage


class TodoModel(QObject):

    def __init__(self):
        self._storage = Storage()
        self._todos = self._storage.todos()

    def todos(self):
        return self._todos

    def add_todo(self, todo_name):
        self._todos.append(todo_name)
        self._storage.add_todo(todo_name)

    def remove_todo(self, todo_name):
        self._todos.remove(todo_name)
        self._storage.remove_todo(todo_name)
