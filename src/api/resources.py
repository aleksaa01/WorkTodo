from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from api.utils import *

class Dispatcher(object):

    def __init__(self, output_queue, token=None):
        self.output_queue = output_queue
        self.token = token
        self.executor = ThreadPoolExecutor()

    def authenticate(self, job_id, username, password):
        future = self.executor.submit(authenticate, username, password)
        self.output_queue.put((job_id, future))

    def get_cards(self, job_id):
        future = self.executor.submit(get_cards, self.token)
        self.output_queue.put((job_id, future))

    def get_tasks(self, job_id):
        future = self.executor.submit(get_tasks, self.token)
        self.output_queue.put((job_id, future))

    def get_preferences(self, job_id):
        future = self.executor.submit(get_preferences, job_id)
        self.output_queue.put((job_id, future))

    def create_card(self, job_id, card):
        future = self.executor.submit(create_card, self.token, card)
        self.output_queue.put((job_id, future))

    def create_task(self, job_id, task):
        future = self.executor.submit(create_task, self.token, task)
        self.output_queue.put((job_id, future))

    def remove_task(self, job_id, task):
        future = self.executor.submit(remove_task, self.token, task)
        self.output_queue.put((job_id, future))

    def modify_task(self, job_id, task):
        future = self.executor.submit(modify_task, self.token, task)
        self.output_queue.put((job_id, future))


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


if __name__ == '__main__':
    import requests
    import json
    from queue import Queue
    data = {'username': 'user1', 'password': 'user1'}
    response = requests.post(urls['authenticate'], json=data)
    print(response.content)
    content = json.loads(response.content)
    token = content['token']
    print(token)

    q = Queue()
    dispatcher = Dispatcher(token, q)
    dispatcher.get_cards(1)
    dispatcher.get_tasks(2)
    dispatcher.get_cards(3)
    dispatcher.get_tasks(4)

    jobs = 4
    while jobs > 0:
        if q.empty():
            continue
        jobs -= 1
        job_id, future = q.get()
        if not future.done():
            q.put((job_id, future))
        result = future.result()
        if isinstance(result, list):
            print('--------', job_id)
            for i in result:
                print(vars(i))
            print('^^^^^^^^')
