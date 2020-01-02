from concurrent.futures import ThreadPoolExecutor
from api.methods import *


class ApiCallDispatcher(object):

    def __init__(self, output_queue, token=None):
        self.output_queue = output_queue
        self.token = token
        self.executor = ThreadPoolExecutor()
        self._job_id_counter = 0

    def authenticate(self, username, password):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(authenticate, username, password)
        self.output_queue.put((jid, future))
        return jid

    def register(self, email, username, password):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(register, email, username, password)
        self.output_queue.put((jid, future))
        return jid

    def get_cards(self):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(get_cards, self.token)
        self.output_queue.put((jid, future))
        return jid

    def get_tasks(self):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(get_tasks, self.token)
        self.output_queue.put((jid, future))
        return jid

    def get_preferences(self):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(get_preferences, self.token)
        self.output_queue.put((jid, future))
        return jid

    def create_card(self, card):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(create_card, self.token, card)
        self.output_queue.put((jid, future))
        return jid

    def create_task(self, task):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(create_task, self.token, task)
        self.output_queue.put((jid, future))
        return jid

    def remove_task(self, task):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(remove_task, self.token, task)
        self.output_queue.put((jid, future))
        return jid

    def modify_task(self, task):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(modify_task, self.token, task)
        self.output_queue.put((jid, future))
        return jid

    def sync(self, file_data, curr_data):
        jid = self._job_id_counter
        self._job_id_counter += 1
        future = self.executor.submit(sync_diff, self.token, file_data, curr_data)
        self.output_queue.put((jid, future))
        return jid



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
