from tasks.objects import Task


class TodosModel(object):

    def __init__(self, name, storage, parent=None):
        super().__init__(parent)

        self.name = name
        self._storage = storage
        self._tasks = None

    def tasks(self):
        if self._tasks is None:
            self._tasks = []
            for raw_json in self._storage.tasks(self.name):
                self._tasks.append(self._build_task(raw_json))
        return self._tasks

    def _build_task(self, raw_json):
        task = Task(
            raw_json['name'],
            raw_json['description'],
            raw_json['start_time'],
            raw_json['end_time']
        )
        return task
