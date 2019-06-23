from PyQt5.QtCore import QObject, pyqtSignal


class Action(QObject):

    signal = pyqtSignal(str)

    def __init__(self, text, icon=None, parent=None):
        super().__init__(None)
        self.text = text
        self.icon = icon
