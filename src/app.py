from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, \
    QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from queues.widgets import QueueWidget, QueueManager, QueueSidebar
from storage import QueueStorage
from widgets import SidebarButton

import random


class AppWindow(QMainWindow):

    def __init__(self, width=600, height=800):
        super().__init__(None)
        self.resize(width, height)

        self.storage = QueueStorage()
        self.storage.debug = True

        self.cw = QWidget(self)  # central widget
        self.layout = QVBoxLayout()

        self.colors = ['red', 'green', 'blue', 'yellow', 'orange']
        self.sidebar = QueueSidebar(self.storage, self.cw)
        self.queue_manager = QueueManager(self.sidebar, self.storage, self.cw)
        self.load_pages()

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.queue_manager)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        self.show()

    def load_pages(self):
        t1 = time.time()
        for name in self.storage.queues():
            self.add_page(name)
        t2 = time.time()
        print('Loading pages took:', t2 - t1)

    def add_page(self, name):
        widget = SidebarButton(name)
        widget.setFixedSize(80, 20)
        self.sidebar.add_widget(widget, name)




if __name__ == '__main__':
    import time
    app_instance = QApplication([])
    app_instance.setStyleSheet(""".SidebarButton{background: transparent;border: 0px solid black; border-bottom: 1px solid red;}
.SidebarButton:checked{border-bottom: 2px solid red; font-weight: 700}
SidebarButton:hover{border-bottom: 3px solid red;}""")

    from resources import icons_rc
    # This actually loads resource file for the first time.
    QPixmap(':')

    win = AppWindow()
    app_instance.exec_()
