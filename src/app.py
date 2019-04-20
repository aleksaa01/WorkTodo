from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout

from widgets import Sidebar


class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__(None)

        self.cw = QWidget(self)  # central widget
        self.cw.setStyleSheet('background: #44ffaa;')
        layout = QVBoxLayout()
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)

        self.show()




if __name__ == '__main__':
    app_instance = QApplication([])
    win = AppWindow()
    app_instance.exec_()
