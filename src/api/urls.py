
DOMAIN = 'http://127.0.0.1'
PORT = 8000


def prepend_domain(urls):
    for key, value in urls.items():
        urls[key] = DOMAIN + ':' + str(PORT) + '/' + value


urls = {
    'cards': 'api/cards/',
    'tasks': 'api/tasks/',
    'preferences': 'api/preferences/',
    'register': 'api/register',
    'authenticate': 'api/token-auth/'
}

prepend_domain(urls)

