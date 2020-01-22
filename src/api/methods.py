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
    task_rid = task.rid
    url = urls['tasks'] + str(task_rid)
    response = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    sc = response.status_code
    assert sc == 204, "Unable to delete task, got {} status code instead of 204".format(sc)


def modify_task(token, task):
    url = urls['tasks']
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=task.to_json())
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


def update_cards(token, card_list):
    url = urls['cards']
    response = requests.put(url, headers={'Authorization': 'Token {}'.format(token)}, json=card_list)
    sc = response.status_code
    # Do something if status code is inappropriate
    return True


def remove_cards(token, card_list):
    url = urls['cards']
    response = requests.delete(url, headers={'Authorization': 'Token {}'.format(token)}, json=card_list)
    sc = response.status_code
    return True


def add_cards(token, card_list):
    url = urls['cards']
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=card_list)
    sc = response.status_code
    return True


def update_tasks(token, task_list):
    url = urls['tasks']
    response = requests.put(url, headers={'Authorization': 'Token {}'.format(token)}, json=task_list)
    sc = response.status_code
    return True


def remove_tasks(token, task_list):
    url = urls['tasks']
    response = requests.delete(url, headers={'Authorization': 'Token {}'.format(token)}, json=task_list)
    sc = response.status_code
    return True


def add_tasks(token, task_list):
    url = urls['tasks']
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=task_list)
    sc = response.status_code
    return True


def update_preferences(token, preference_list):
    url = urls['preferences']
    reponse = requests.put(url, headers={'Authorization': 'Token {}'.format(token)}, json=preference_list)
    sc = response.status_code
    return True


def remove_preferences(token, preference_list):
    url = urls['preferences']
    response = requests.delete(url, headers={'Authorization': 'Token {}'.format(token)}, json=preference_list)
    sc = response.status_code
    return True


def add_preferences(token, preference_list):
    url = urls['preferences']
    response = requests.post(url, headers={'Authorization': 'Token {}'.format(token)}, json=preference_list)
    sc = response.status_code
    return True


def authenticate(username, password):
    url = urls['authenticate']
    data = {'username': username, 'password': password}
    response = requests.post(url, json=data)
    return json.loads(response.content)['token']


def register(email, username, password):
    url = urls['register']
    data = {'email': email, 'username': username, 'password': password}
    response = requests.post(url, json=data)
    sc = response.status_code
    raw = response.content
    content = json.loads(raw) if len(raw) > 0 else ''
    if isinstance(content, str):
        return sc, content
    return sc, content[0]

def sync_diff(token, file_data, curr_data):
    file_cards = {c['rid']:c for c in file_data['cards']}
    file_tasks = {}
    for task in file_data['tasks']:
        file_tasks[task['rid']] = task
    file_prefs = {p['rid']:p for p in file_data['preferences']}

    curr_cards = {c['rid']: c for c in curr_data['cards']}
    curr_tasks = {}
    for task in curr_data['tasks']:
        curr_tasks[task['rid']] = task
    curr_prefs = {p['rid']: p for p in curr_data['preferences']}

    card_updates, card_removes, card_adds = _find_resource_diff(file_cards, curr_cards)
    task_updates, task_removes, task_adds = _find_resource_diff(file_tasks, curr_tasks)
    pref_updates, pref_removes, pref_adds = _find_resource_diff(file_prefs, curr_prefs)

    update_cards(token, card_updates) if card_updates else True
    remove_cards(token, card_removes) if card_removes else True
    add_cards(token, card_adds) if card_adds else True
    update_tasks(token, task_updates) if task_updates else True
    remove_tasks(token, task_removes) if task_removes else True
    add_tasks(token, task_adds) if task_adds else True
    update_preferences(token, pref_updates) if pref_updates else True
    remove_preferences(token, pref_removes) if pref_removes else True
    add_preferences(token, pref_adds) if pref_adds else True

    return True


def _find_resource_diff(old_resource_dict, new_resource_dict):
    res_updates = []
    res_removes = []
    res_adds = []
    
    for old_res in old_resource_dict.values():
        if old_res['rid'] in new_resource_dict:
            new_res = new_resource_dict[old_res['rid']]
            if old_res != new_res:
                res_updates.append(new_res)
        else:
            res_removes.append(old_res['rid'])
    
    for new_res in new_resource_dict.values():
        if new_res['rid'] not in old_resource_dict:
            res_adds.append(new_res)
    
    return res_updates, res_removes, res_adds
