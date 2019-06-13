class Task(object):

    def __init__(self, name, description, start_time, end_time):
        self._name = name
        self._description = description
        self._start_time = start_time
        self._end_time = end_time

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, new_description):
        self._description = new_description

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, new_start_time):
        self._start_time = new_start_time

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, new_end_time):
        self._end_time = new_end_time
