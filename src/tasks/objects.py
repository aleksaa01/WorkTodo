import datetime


def create_task_object(description):
    task_object = TaskObject()
    task_object.description = description
    task_object.date = datetime.datetime.now().timestamp()
    return task_object


class TaskObject(object):

    def __init__(self, json_object):
        if not isinstance(json_object, dict):
            raise TypeError('Expected dict type, got {} instead'.format(json_object))

        self.description = json_object['description']
        self.date = json_object['date']

    def to_json(self):
        return {'description': self.description, 'date': self.date}