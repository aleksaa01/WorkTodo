from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton

from widgets import Sidebar

import random


class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__(None)

        self.cw = QWidget(self)  # central widget
        self.cw.setStyleSheet('background: #44ffaa;')
        layout = QVBoxLayout()

        self.colors = ['red', 'green', 'blue', 'yellow', 'orange']
        self.sidebar = Sidebar()
        # TODO: Load pages from storage
        self.add_page('Matematika')
        self.add_page('Python')
        self.add_page('Vezbanje')
        self.add_page('Skola')

        layout.addWidget(self.sidebar)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)

        self.show()

    def add_page(self, name):
        widget = QPushButton(name)
        widget.setFixedSize(80, 40)
        widget.setStyleSheet('background: {}'.format(random.choice(self.colors)))
        self.sidebar.add_widget(widget)




if __name__ == '__main__':
    app_instance = QApplication([])
    win = AppWindow()
    app_instance.exec_()
