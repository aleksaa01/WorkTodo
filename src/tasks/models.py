from PyQt5.QtCore import QObject
from api.resources import TaskResource
from storage import Storage


class TasksModel(QObject):

    def __init__(self, storage, card_rid):
        self._st = storage
        self.crid = card_rid
        self._last_rid = None

    def data(self):
        return [(task.rid, task.description, task.created)
                for task in self._st.tasks[self.crid]]

    def add(self, text):
        # Should I set position of the task here ? Seems unnecessary though.
        task = TaskResource(description=text)
        new_rid = self._get_new_rid()
        task.rid = new_rid
        self._st.add_task(self.crid, task)

    def remove(self, task_index):
        self._st.pop_task(self.crid, task_index)

    def move(self, old_idx, new_idx):
        self._st.move_task(self.crid, old_idx, new_idx)

    def update(self, task_index, text):
        task = self._st.get_task(task_index)
        task.description = text
        self._st.update_task(task)

    def _get_new_rid(self):
        new_rid = self._last_rid + 1 if self._last_rid else 0
        while True:
            if new_rid in self._st.task_rids:
                new_rid += 1
            else:
                return new_rid
