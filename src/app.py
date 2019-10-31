from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from cards.widgets import CardWidget, CardWidgetManager, CardSidebar
from cards.models import CardModel
from widgets import SaveDialog, CredentialsScreen
from storage import Storage
from shortcuts import set_shortcut


class AppWindow(QMainWindow):

    def __init__(self, width=800, height=800):
        super().__init__(None)
        self.resize(width, height)

        self.storage = Storage()
        self.storage.debug = False
        if not self.storage.is_authenticated():
            # show login/register dialog
            pass

        # Shortcuts
        set_shortcut('save', self.storage.save, self)
        set_shortcut('quit', self.close, self)
        ###########

        self.cw = QWidget(self)  # central widget
        self.layout = QVBoxLayout()
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        if not storage.is_authenticated():
            creds_screen = CredentialsScreen(login_func=self.storage.authenticate)
            creds_screen.logged_in.connect(self.clear_and_load)
            self.layout.addWidget(creds_screen)
        else:
            self.load()

        self.show()

    def load(self):
        card_model = CardModel(self.storage)
        self.sidebar = CardSidebar(card_model, parent=self.cw)
        self.manager = CardWidgetManager(card_model, self.cw)

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.manager)

    def clear_and_load(self):
        #TODO: test if takeAt(last index) is faster than takeAt(0)
        item = self.layout.takeAt(0)
        while item != None:
            item.deleteLater()
            item = self.layout.takeAt(0)
        self.load()

    def closeEvent(self, event):
        if self.storage.saved is False:
            dialog = SaveDialog(self)
            dialog.accepted.connect(self.storage.save)
            dialog.exec()

        super().closeEvent(event)


if __name__ == '__main__':
    app_instance = QApplication([])
    app_instance.setStyleSheet(""".SidebarButton{background: transparent;border: 0px solid black; border-bottom: 1px solid red;}
.SidebarButton:checked{border-bottom: 2px solid red; font-weight: 700}
SidebarButton:hover{border-bottom: 3px solid red;}
""")

    from resources import icons_rc
    # This actually loads resource file for the first time.
    QPixmap(':')

    win = AppWindow()
    app_instance.exec_()
