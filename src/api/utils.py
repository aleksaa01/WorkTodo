from api.urls import urls
from api.resources import CardResource, TaskResource, PreferenceResource
import requests
import json


def get_cards(token):
    url = urls['cards']
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 200, 'Unable to get cards, got {} status code instead of 200'.format(sc)
    cards_resource = json.loads(response.content)
    return [CardResource.from_json(resource) for resource in cards_resource]


def remove_task(token, task):
    task_id = task.id
    url = urls['tasks'] + str(task_id)
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 204, "Unable to delete task, got {} status code instead of 204".format(sc)


def modify_task(token, task):
    url = urls['tasks']
    resposne = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=task.to_json())
    sc = response.status_code
    assert sc == 200, "Unable to modify task, got {} status code instead of 200".format(sc)


def get_tasks(token):
    url = urls['tasks']
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 200, 'Unable to get tasks, got {} status code instead of 200'.format(sc)
    tasks_resource = json.loads(response.content)
    return [TaskResource.from_json(resource) for resource in tasks_resource]

def get_preferences(token):
    url = urls['preferences']
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    prefs_resource = json.loads(response.content)
    return [PreferenceResource.from_json(resource) for resource in prefs_resource]

def create_card(token, card):
    url = urls['cards']
    data = card.to_json()
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=data)
    sc = response.status_code
    assert sc == 201, 'Unable to create card, got {} status code instead of 201'.format(sc)


def create_task(token, task):
    url = urls['tasks']
    data = task.to_json()
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=data)
    sc = response.status_code
    assert sc == 201, 'Unable to create task, got {} status code instead of 201'.format(sc)
    return TaskResource.from_json(json.loads(response.content))

def authenticate(username, password):
    url = urls['authenticate']
    data = {'username': username, 'password': password}
    response = requests.post(url, json=data)
    return json.loads(response.content)['token']
