from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton

from widgets import Sidebar, QueueWidget
from storage import QueueStorage

import random


class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__(None)
        self.storage = QueueStorage()
        self.queues = {}

        self.cw = QWidget(self)  # central widget
        self.cw.setStyleSheet('background: #44ffaa;')
        self.layout = QVBoxLayout()

        self.colors = ['red', 'green', 'blue', 'yellow', 'orange']
        self.sidebar = Sidebar()
        self.load_pages()

        self.layout.addWidget(self.sidebar)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        self.show()

    def load_pages(self):
        for name in self.storage.queues():
            self.add_page(name)

    def add_page(self, name):
        widget = QPushButton(name)
        widget.clicked.connect(lambda: self.show_queue(name))
        widget.setFixedSize(80, 40)
        widget.setStyleSheet('background: {}'.format(random.choice(self.colors)))
        self.sidebar.add_widget(widget)

    def show_queue(self, name):
        print('Queue name:', name)
        if name in self.queues:
            qs = self.queues[name]
        else:
            qs = QueueWidget(name, self.storage, self.cw)
            self.queues[name] = qs

        qs.load()
        self.layout.addWidget(qs)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)




if __name__ == '__main__':
    app_instance = QApplication([])
    win = AppWindow()
    app_instance.exec_()
