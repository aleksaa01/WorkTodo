from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from cards.widgets import CardWidget, CardWidgetManager, CardSidebar, SidebarContainer
from cards.models import CardsModel
from widgets import SaveDialog, CredentialsScreen
from storage import Storage
from shortcuts import set_shortcut


class AppWindow(QMainWindow):

    def __init__(self, width=800, height=800):
        super().__init__(None)
        self.resize(width, height)

        self.storage = Storage()
        self.storage.debug = False

        # Shortcuts
        set_shortcut('save', self.save, self)
        set_shortcut('quit', self.close, self)
        ###########

        self.cw = QWidget(self)  # central widget
        self.layout = QVBoxLayout()
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        if not self.storage.is_authenticated():
            creds_screen = CredentialsScreen(self.storage.authenticate, self.storage.register, parent=self.cw)
            creds_screen.logged_in.connect(self.clear_and_load)
            self.layout.addWidget(creds_screen)
        else:
            self.load()
            self.loaded = True

        self.show()

    def load(self):
        self.storage.fetch_all()
        card_model = CardsModel(self.storage)
        sidebar = CardSidebar(card_model, parent=self.cw)
        sidebar.logout.connect(self.logout)
        self.sidebar_container = SidebarContainer(sidebar)
        self.manager = CardWidgetManager(card_model, self.cw)

        self.layout.addWidget(self.sidebar_container)
        self.layout.addWidget(self.manager)

    def clear_and_load(self):
        self.clear()
        self.load()

    def clear(self):
        # TODO: test if takeAt(last index) is faster than takeAt(0)
        item = self.layout.takeAt(0)
        while item != None:
            item.widget().deleteLater()
            item = self.layout.takeAt(0)

    def logout(self):
        self.storage.remove_token()
        if self.storage.saved is False:
            dialog = SaveDialog(self)
            result = dialog.exec()
            if result == dialog.Accepted:
                self.save()
            elif result == dialog.Canceled:
                return
        self.clear()
        creds_screen = CredentialsScreen(self.storage.authenticate, self.storage.register, parent=self.cw)
        creds_screen.logged_in.connect(self.clear_and_load)
        self.layout.addWidget(creds_screen)
        self.loaded = False

    def closeEvent(self, event):
        if self.storage.saved is False and self.loaded is True:
            dialog = SaveDialog(self)
            result = dialog.exec()
            if result == dialog.Accepted:
                self.save()
            elif result == dialog.Canceled:
                event.ignore()

    def save(self):
        self.storage.sync()
        self.storage.save()


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
