from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, \
    QPushButton, QSizePolicy, QScrollArea
from PyQt5.QtGui import QIcon, QPixmap
from todos.widgets import TodoWidget, TodoManager, TodoSidebar, CustomListWidgetManager, \
    TodoSidebar
from todos.models import TodoModel
from storage import Storage

from shortcuts import set_shortcut

import random


class AppWindow(QMainWindow):

    def __init__(self, width=800, height=800):
        super().__init__(None)
        self.resize(width, height)

        self.storage = Storage()
        self.storage.debug = False

        # FIXME: Storage is not synchronized with models.
        # Shortcuts
        set_shortcut('save', self.storage.save, self)
        set_shortcut('quit', self.close, self)
        ###########

        self.cw = QWidget(self)  # central widget
        self.layout = QVBoxLayout()

        self.colors = ['red', 'green', 'blue', 'yellow', 'orange']
        todo_model = TodoModel()
        self.sidebar = TodoSidebar(model=todo_model, parent=self.cw)
        self.manager = CustomListWidgetManager(todo_model, self.sidebar, self.cw)

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.manager)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        self.show()


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
