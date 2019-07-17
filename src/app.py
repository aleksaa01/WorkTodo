from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from cards.widgets import CardWidget, CardWidgetManager, CardSidebar
from cards.models import CardModel
from widgets import SaveDialog
from storage import Storage
from shortcuts import set_shortcut


class AppWindow(QMainWindow):

    def __init__(self, width=800, height=800):
        super().__init__(None)
        self.resize(width, height)

        self.storage = Storage()
        self.storage.debug = False

        # Shortcuts
        set_shortcut('save', self.storage.save, self)
        set_shortcut('quit', self.close, self)
        ###########

        self.cw = QWidget(self)  # central widget
        self.layout = QVBoxLayout()

        card_model = CardModel()
        self.sidebar = CardSidebar(model=card_model, parent=self.cw)
        self.manager = CardWidgetManager(self.sidebar, self.cw)

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.manager)
        self.cw.setLayout(self.layout)
        self.setCentralWidget(self.cw)

        self.show()

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
QListWidget::item{background: transparent;}
.TaskWidget{background: #f2f2f2; border: 1px solid #cccccc;}""")

    from resources import icons_rc
    # This actually loads resource file for the first time.
    QPixmap(':')

    win = AppWindow()
    app_instance.exec_()
