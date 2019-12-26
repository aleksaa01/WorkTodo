from PyQt5.QtCore import QObject
from api.resources import TaskResource
from storage import Storage


class TasksModel(object):

    def __init__(self, storage, card_rid):
        self._st = storage
        self.crid = card_rid
        self._last_rid = None

    def data(self, index=None):
        if index is None:
            return [(task.rid, task.description, task.created)
                    for task in self._st.tasks(self.crid)]
        task = self._st.get_task(self.crid, index)
        return (task.rid, task.description, task.created)

    def add(self, text, created):
        # Should I set position of the task here ? Seems unnecessary though.
        new_rid = self._get_new_rid()
        task = TaskResource(rid=new_rid, description=text,
                            card_rid=self.crid, created=created)
        self._st.add_task(self.crid, task)
        return new_rid

    def remove(self, task_index):
        self._st.pop_task(self.crid, task_index)

    def move(self, old_idx, new_idx):
        self._st.move_task(self.crid, old_idx, new_idx)

    def update(self, task_index, text, created_at=None):
        task = self._st.get_task(self.crid, task_index)
        task.description = text
        if created_at:
            task.created = created_at
        self._st.update_task(self.crid, task_index, task)

    def find(self, task_rid):
        for idx, task in enumerate(self._st.tasks(self.crid)):
            if task.rid == task_rid:
                return idx
        return -1

    def insert(self, index, text, created):
        new_rid = self._get_new_rid()
        task = TaskResource(rid=new_rid, description=text,
                            card_rid=self.crid, created=created)
        self._st.insert_task(self.crid, index, task)
        return new_rid


    def _get_new_rid(self):
        new_rid = self._last_rid + 1 if self._last_rid else 0
        while True:
            if new_rid in self._st.task_rids:
                new_rid += 1
            else:
                return new_rid

    def __getitem__(self, idx):
        task = self._st.get_task(self.crid, idx)
        return (task.rid, taks.description, task.created)

    def __len__(self):
        return len(self._st.tasks(self.crid))
