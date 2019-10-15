from datetime import datetime


class ResourceBase(object):

    @classmethod
    def from_json(cls, json_resource):
        return cls(**json_resource)

    def to_json(self):
        return vars(self)


class CardResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.name = kwargs['name']
        # For perfermance reasons, you can update position just before API synchronization
        self.position = kwargs['position']
        self.tasks = kwargs.get('tasks', [])
        self.preferences = kwargs.get('preferenecs', [])


class TaskResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.description = kwargs['description']
        # For perfermance reasons, you can update position just before API synchronization
        self.position = kwargs['position']
        self.card_rid = kwargs['card_rid']
        self.created = kwargs.get('created', datetime.now().timestamp())


class PreferenceResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.card_rid = kwargs['card_rid']
        self.warning_time = kwargs['warning_time']
        self.danger_time = kwargs['danger_time']
        self.show_date = kwargs['show_date']
