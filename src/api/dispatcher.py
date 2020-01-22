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
