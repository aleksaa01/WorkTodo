from datetime import datetime
from urls import urls
import requests
import json
from concurrent.futures import ThreadPoolExecutor


def _create_task(task, token):
    url = urls['tasks']
    data = task.to_json()
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=data)
    sc = response.status_code
    assert sc == 201, 'Unable to create task, got {} status code instead of 201'.format(sc)
    return TaskResource.from_json(json.loads(response.content))


def _get_cards(token):
    url = urls['cards']
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 200, 'Unable to get cards, got {} status code instead of 200'.format(sc)
    cards_resource = json.loads(response.content)
    return [CardResource.from_json(resource) for resource in cards_resource]


def _remove_task(token, task):
    task_id = task.id
    url = urls['tasks'] + str(task_id)
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 204, "Unable to delete task, got {} status code instead of 204".format(sc)


def _modify_task(token, task):
    url = urls['tasks']
    resposne = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=task.to_json())
    sc = response.status_code
    assert sc == 200, "Unable to modify task, got {} status code instead of 200".format(sc)


def _get_tasks(token):
    url = urls['tasks']
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 200, 'Unable to get tasks, got {} status code instead of 200'.format(sc)
    tasks_resource = json.loads(response.content)
    return [TaskResource.from_json(resource) for resource in tasks_resource]

def _create_card(token, card):
    url = urls['cards']
    data = card.to_json()
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=data)


class Dispatcher(object):

    def __init__(self, token, output_queue):
        self.token = token
        self.output_queue = output_queue
        self.executor = ThreadPoolExecutor()

    def get_cards(self, job_id):
        future = self.executor.submit(_get_cards, self.token)
        self.output_queue.put((job_id, future))

    def get_tasks(self, job_id):
        future = self.executor.submit(_get_tasks, self.token)
        self.output_queue.put((job_id, future))

    def create_card(self, job_id, card):
        future = self.executor.submit(_create_card, self.token, card)

    def create_task(self, job_id, task):
        future = self.executor.submit(_create_task, self.token, task)
        self.output_queue.put((job_id, future))

    def remove_task(self, job_id, task):
        future = self.executor.submit(_remove_task, self.token, task)
        self.output_queue.put((job_id, future))

    def modify_task(self, job_id, task):
        future = self.executor.submit(_modify_task, self.token, task)
        self.output_queue.put((job_id, future))


class ResourceBase(object):

    @classmethod
    def from_json(cls, json_resource):
        return cls(**json_resource)

    def to_json(self):
        return {k: v for k, v in vars(self) if k != 'id'}



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
