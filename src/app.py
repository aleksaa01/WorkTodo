from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton, QSizePolicy

from widgets import Sidebar
from queue.widgets import QueueWidget, QueueManager
from storage import QueueStorage

import random


class AppWindow(QMainWindow):

    def __init__(self, width=500, height=400):
        super().__init__(None)
        self.resize(width, height)

        self.storage = QueueStorage()

        self.cw = QWidget(self)  # central widget
        self.cw.setStyleSheet('background: #44ffaa;')
        self.layout = QVBoxLayout()

        self.colors = ['red', 'green', 'blue', 'yellow', 'orange']
        self.sidebar = Sidebar(self.cw)
        self.queue_manager = QueueManager(self.sidebar, self.storage, self.cw)
        self.load_pages()

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.queue_manager)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        self.show()

    def load_pages(self):
        for name in self.storage.queues():
            self.add_page(name)

    def add_page(self, name):
        widget = QPushButton(name)
        widget.setFixedSize(80, 40)
        widget.setStyleSheet('background: {}'.format(random.choice(self.colors)))
        self.sidebar.add_widget(widget, name)




if __name__ == '__main__':
    app_instance = QApplication([])
    win = AppWindow()
    app_instance.exec_()
