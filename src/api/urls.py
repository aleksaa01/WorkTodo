
DOMAIN = 'https://avram.pythonanywhere.com'


def prepend_domain(urls):
    for key, value in urls.items():
        urls[key] = DOMAIN + '/' + value


urls = {
    'cards': 'api/cards/',
    'tasks': 'api/tasks/',
    'preferences': 'api/preferences/',
    'register': 'api/register/',
    'authenticate': 'api/token-auth/'
}

prepend_domain(urls)

