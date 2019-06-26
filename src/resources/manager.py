from PyQt5.QtGui import QIcon, QPixmap


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, *kwargs)
        return cls._instance


class ResourceManager(metaclass=Singleton):

    def __init__(self):
        self.resource_mapper = {
            'delete_icon': None,
            'add_icon': None,
            'select_icon': None,
            'rules_icon': None,
        }

    def icon_exists(self, icon_name):
        if icon_name in self.resource_mapper:
            return True
        return False

    def get_icon(self, icon_name):
        icon = self.resource_mapper[icon_name]

        # cache it if it's not already cached
        if icon is None:
            icon = self.load_icon(icon_name)
            self.resource_mapper[icon_name] = icon

        return icon

    def load_icon(self, icon_name, icon_format='png'):
        return QIcon(QPixmap(':images/{}.{}'.format(icon_name, icon_format)))


if __name__ != '__main__':
    print('Called another time')
    resource = ResourceManager()