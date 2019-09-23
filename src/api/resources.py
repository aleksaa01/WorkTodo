from datetime import datetime


class ResourceBase(object):

    @classmethod
    def from_json(cls, json_resource):
        return cls(**json_resource)

    def to_json(self):
        return vars(self)


class CardResource(ResourceBase):

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.name = kwargs['name']
        self.tasks = kwargs.get('tasks', [])
        self.preferences = kwargs.get('preferenecs', [])


class TaskResource(ResourceBase):

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.description = kwargs['description']
        self.card_id = kwargs['card_id']
        self.created = kwargs.get('created', datetime.now().timestamp())


class PreferenceResource(ResourceBase):

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.card_id = kwargs['card_id']
        self.warning_time = kwargs['warning_time']
        self.danger_time = kwargs['danger_time']
        self.show_date = kwargs['show_date']
