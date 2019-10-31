from PyQt5.QtCore import QObject, pyqtSignal, QPoint


class Action(QObject):

    signal = pyqtSignal(QPoint)

    def __init__(self, text, icon=None):
        super().__init__(None)
        self.text = text
        self.icon = icon
