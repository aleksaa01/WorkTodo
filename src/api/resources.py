from datetime import datetime


class ResourceBase(object):
    """
    #field_map: Use it if you want to name resource fields differently
        from how are they named in the api.
    """
    field_map = None

    @classmethod
    def from_json(cls, json_resource):
        return cls(**json_resource)

    def to_json(self):
        if self.field_map is None:
            return vars(self)

        output = {}
        for field_name, val in vars(self):
            if field_name in self.field_map:
                new_field_name = self.field_map[field_name]
                output[new_field_name] = val
            else:
                output[field_name] = val
        return output


class CardResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.name = kwargs['name']
        # For perfermance reasons, you can update position just before API synchronization
        self.position = kwargs['position']


class TaskResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.description = kwargs['description']
        # For perfermance reasons, you can update position just before API synchronization
        self.position = kwargs.get('position', None)
        self.card_rid = kwargs['card_rid']
        self.created = kwargs.get('created', datetime.now().timestamp())


class PreferenceResource(ResourceBase):

    def __init__(self, **kwargs):
        self.rid = kwargs['rid']
        self.card_rid = kwargs['card_rid']
        self.warning_time = kwargs['warning_time']
        self.danger_time = kwargs['danger_time']
        self.show_date = kwargs['show_date']
