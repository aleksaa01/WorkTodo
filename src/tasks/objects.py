import datetime


def create_task_object(description):
    date = datetime.datetime.now().timestamp()
    task_object = TaskObject()
    task_object.description = description
    task_object.date = date
    return task_object


class TaskObject(object):

    def __init__(self, json_object=None):
        if json_object is None:
            self.description = None
            self.date = None
            return
        elif isinstance(json_object, dict):
            self.description = json_object['description']
            self.date = json_object['date']
        else:
            raise TypeError('Expected dict or None, got {} instead'.format(json_object))

    def to_json(self):
        return {'description': self.description, 'date': self.date}