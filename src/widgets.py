from PyQt5.QtWidgets import QWidget, QLayout, QPushButton, QScrollArea, QSizePolicy, \
    QHBoxLayout, QSpinBox, QLabel, QDialog, QVBoxLayout, QStackedWidget, QLineEdit, \
    QFrame
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal, QLine, QEvent, QPropertyAnimation

from api.methods import NoInternetConnection, InvalidCredentials

import re


EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class FlowLayout(QLayout):
    def __init__(self, max_height=None, parent=None, margin=0, spacex=5, spacey=5):
        super().__init__(parent)

        self.max_height = max_height if max_height else 10000

        if parent:
            self.setMargin(margin)

        self.margin = margin

        self.spacex = spacex
        self.spacey = spacey

        self.itemList = []

    def __del__(self):
        self.itemList.clear()

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def setGeometry(self, rect):
        super().setGeometry(rect)

        final_height = self.resize_layout(rect)
        parent = self.parent()
        if final_height != parent.height() and final_height <= self.max_height:
            parent.setFixedHeight(final_height)
        elif final_height == parent.height():
            # TODO: Resize items to fit into max_height
            pass

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        # Returns minimum size of the layout.
        # Implement to ensure your layout isn't resized to zero size if there is too little space
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.margin, 2 * self.margin)
        return size

    def resize_layout(self, rect):
        # (x, y) - starting position of this layout
        x = rect.x()
        y = rect.y()
        line_height = 0

        sx = self.spacex
        sy = self.spacey
        for item in self.itemList:
            item_size_hint = item.sizeHint()
            item_width = item_size_hint.width()
            item_height = item_size_hint.height()

            nextx = x + item_width + sx
            # print('x, item.sizeHint(), sx, nextxm, rect: ', x, item.sizeHint(), sx, nextx, rect)
            if nextx - sx > rect.right() and line_height > 0:
                # print('Go to new line...')
                x = rect.x()
                y = y + line_height + sy
                nextx = x + item_width + sx
                # going to new line, set line_height to 0.
                line_height = 0

            item.setGeometry(QRect(QPoint(x, y), item_size_hint))

            x = nextx
            # Check if this item has the biggest height of all the items in current line.
            line_height = max(line_height, item_height)
        return y + line_height + sy

    def resize_children(self):
        for item in self.itemList:
            widget = item.widget()
            w = widget.width()
            h = widget.height()
            widget.setFixedWidth(w - w * 0.1)
            widget.setFixedHeight(h)
            widget.setText(widget.text())
        self.resize_layout(self.geometry())


class SidebarCardHolder(QFrame):

    clicked = pyqtSignal(int)

    def __init__(self, wgt_id, text, parent=None):
        super().__init__(parent)
        # self.setFrameShape(QFrame.StyledPanel)
        # self.setFrameShadow(QFrame.Plain)

        self.widget_id = wgt_id
        self.setMouseTracking(True)

        self.text_lbl = QLabel(text)
        self.bottom_line = QFrame()
        self.bottom_line.setFrameShape(QFrame.HLine)
        self.bottom_line.setFrameShadow(QFrame.Sunken)
        self.bottom_line.setFixedHeight(1)
        self.bottom_line.setObjectName('CardHolderBLine')
        self.bottom_line.setStyleSheet('#CardHolderBLine{background: blue;}')

        mlayout = QVBoxLayout()
        mlayout.setContentsMargins(0,0,0,0)
        mlayout.addWidget(self.text_lbl, 0, Qt.AlignCenter)
        mlayout.addWidget(self.bottom_line, 0, Qt.AlignCenter)
        self.setLayout(mlayout)

        size_hint = self.sizeHint()
        # Needed because of hover visuals when card-holder is triggered(displayed).
        size_hint.setHeight(size_hint.height() + 1)
        self.setFixedSize(size_hint)

        self.anim = QPropertyAnimation(self.bottom_line, b'minimumWidth')
        self.anim.setDuration(300)
        self.triggered = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.widget_id)
        self.triggered = not self.triggered
        if self.triggered:
            self.anim.stop()
            self.bottom_line.setFixedHeight(2)
            self.anim.setStartValue(self.bottom_line.width())
            self.anim.setEndValue(self.width() + 10)
            self.anim.start()
        else:
            self.bottom_line.setFixedHeight(1)


    def enterEvent(self, event):
        if self.triggered:
            self.bottom_line.setFixedHeight(2)
        else:
            self.anim.stop()
            self.anim.setStartValue(self.bottom_line.width())
            self.anim.setEndValue(self.width() + 10)
            self.anim.start()

    def leaveEvent(self, event):
        if self.triggered:
            self.bottom_line.setFixedHeight(1)
        else:
            self.anim.stop()
            self.anim.setStartValue(self.bottom_line.width())
            self.anim.setEndValue(0)
            self.anim.start()


class Sidebar(QScrollArea):

    itemclicked = pyqtSignal(str)

    def __init__(self, model=None, max_height=100, parent=None):
        super().__init__(parent)

        self.setMaximumHeight(max_height)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.sidebar_widget = QWidget(self)
        self.sidebar_layout = FlowLayout()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.setWidget(self.sidebar_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)

        self.model = model
        self.load()

    def load(self):
        raise NotImplementedError('load method not implemented.')

    def add_widget(self, widget):
        print('Adding new widget...')
        widget.clicked.connect(self.item_clicked)
        self.sidebar_layout.addWidget(widget)

    def remove_widget(self, id):
        # assumes that widgets have id attribute set
        index = 0
        item = self.sidebar_layout.itemAt(index)
        widget = item.widget()
        while widget:
            if widget.widget_id == id:
                item = self.sidebar_layout.takeAt(index)
                widget = item.widget()
                widget.deleteLater()
                return
            index += 1
            widget = self.sidebar_layout.itemAt(index).widget()

        assert False, 'Widget with id {} is not present'.format(id)

    def item_clicked(self, widget_id):
        self.itemclicked.emit(widget_id)

    def create_widget(self, widget_id, widget_text):
        widget = SidebarCardHolder(widget_id, widget_text)
        min_width = 80
        preferred_width = widget.sizeHint().width() + 20
        width = max(min_width, preferred_width)
        widget.setMinimumWidth(width)
        return widget


class TimeEdit(QWidget):

    def __init__(self, seconds, parent=None):
        super().__init__(parent)
        if seconds is None:
            seconds = 0

        hours, minutes = 0, 0
        if seconds > 0:
            hours = seconds // 3600
            seconds -= (hours * 3600)
        if seconds > 0:
            minutes = seconds // 60
            seconds -= (minutes * 60)

        self._hours = QSpinBox(self)
        self._hours.setValue(hours)
        self._minutes = QSpinBox(self)
        self._minutes.setValue(minutes)
        self._seconds = QSpinBox(self)
        self._seconds.setValue(seconds)

        mlayout = QHBoxLayout()
        mlayout.addWidget(QLabel("Hours:"))
        mlayout.addWidget(self._hours)
        mlayout.addWidget(QLabel("Minutes:"))
        mlayout.addWidget(self._minutes)
        mlayout.addWidget(QLabel("Seconds:"))
        mlayout.addWidget(self._seconds)
        self.setLayout(mlayout)

    def time(self):
        h = int(self._hours.text())
        m = int(self._minutes.text())
        s = int(self._seconds.text())

        return (h, m, s)

    def seconds(self):
        h, m, s = self.time()
        return s + m * 60 + h * 3600


class SaveDialog(QDialog):

    Accepted = 1
    Rejected = 0
    Canceled = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Save')

        self.message = QLabel("You have unsaved changes.")

        self.savebtn = QPushButton("Save")
        self.savebtn.clicked.connect(lambda: self.accept(True))
        self.nosavebtn = QPushButton("Don't save")
        self.nosavebtn.clicked.connect(lambda: self.reject(True))
        self.cancelbtn = QPushButton("Cancel")
        self.cancelbtn.clicked.connect(lambda: self.close(True))

        btnlayout = QHBoxLayout()
        btnlayout.addWidget(self.savebtn)
        btnlayout.addWidget(self.nosavebtn)
        btnlayout.addWidget(self.cancelbtn)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.message)
        mlayout.addLayout(btnlayout)
        self.setLayout(mlayout)

        self._user_choice = None

    def accept(self, set_result=False):
        if set_result is True:
            self._user_choice = self.Accepted
        super().accept()

    def reject(self, set_result=False):
        if set_result is True:
            self._user_choice = self.Rejected
        super().reject()

    def close(self, set_result=False):
        if set_result is True:
            self._user_choice = self.Canceled
        super().close()

    def exec(self, *args, **kwargs):
        super().exec(*args, **kwargs)
        return self._user_choice


class CredentialsScreen(QWidget):

    logged_in = pyqtSignal()

    def __init__(self, login_func, register_func, parent=None):
        super().__init__(parent)
        self.login_func = login_func
        self.register_func = register_func
        self.mlayout = QVBoxLayout()
        self.sw = QStackedWidget(self)

        main_creds_page = MainCredentialsPage(self)
        main_creds_page.action_chosen.connect(self.switch_page)
        login_page = LoginPage(self)
        login_page.login.connect(self.login)
        login_page.action_chosen.connect(self.switch_page)
        reg_page = RegisterPage(self)
        reg_page.on_register.connect(self.register)
        reg_page.action_chosen.connect(self.switch_page)

        self.sw.addWidget(main_creds_page)
        self.sw.addWidget(reg_page)
        self.sw.addWidget(login_page)
        self.sw.setCurrentIndex(0)

        self.mlayout.addWidget(self.sw)
        self.setLayout(self.mlayout)

    def switch_page(self, page_idx):
        self.sw.setCurrentIndex(page_idx)

    def login(self, callback, username, password):
        result = self.login_func(username, password)
        if result is True:
            self.logged_in.emit()
        elif result == NoInternetConnection:
            callback('No internet connection')
        elif result == InvalidCredentials:
            callback('Wrong username or password')
        else:
            callback(result)

    def register(self, callback, email, username, password):
        result = self.register_func(email, username, password)
        if result is True:
            self.sw.setCurrentIndex(0)
        elif result == NoInternetConnection:
            callback('No internet connection')
        else:
            callback(result)


class MainCredentialsPage(QWidget):

    action_chosen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        reg_btn = QPushButton('Register')
        reg_btn.setMinimumSize(180, 60)
        reg_btn.clicked.connect(lambda: self.emit_action(1))
        log_btn = QPushButton('Login')
        log_btn.setMinimumSize(180, 60)
        log_btn.clicked.connect(lambda: self.emit_action(2))

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        layout.addWidget(reg_btn)
        layout.addWidget(log_btn)
        self.setLayout(layout)

    def emit_action(self, action_num):
        self.action_chosen.emit(action_num)


class LoginPage(QWidget):

    login = pyqtSignal(object, str, str)
    action_chosen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        outer_container = QWidget()
        outer_container.setFixedSize(400, 400)
        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setFixedSize(300, 25)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText('Password')
        self.password.setFixedSize(300, 25)
        self.error_reporter = QLabel()
        self.error_reporter.setStyleSheet('color: red;')
        self.error_reporter.setFixedSize(300, 25)
        self.login_btn = QPushButton('Login')
        self.login_btn.clicked.connect(self.emit)
        self.login_btn.setFixedSize(100, 30)
        back_btn = QPushButton('Back')
        back_btn.clicked.connect(lambda: self.action_chosen.emit(0))
        back_btn.setFixedSize(100, 30)

        mlayout = QVBoxLayout()
        mlayout.setAlignment(Qt.AlignCenter)
        mlayout.addWidget(outer_container)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.username, 0, Qt.AlignHCenter)
        layout.addWidget(self.password, 0, Qt.AlignHCenter)
        layout.addWidget(self.error_reporter, 0, Qt.AlignCenter)
        layout.insertSpacing(2, 20)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)

        outer_container.setLayout(layout)
        self.setLayout(mlayout)

    def emit(self):
        usr = self.username.text()
        psw = self.password.text()
        # Just in case, delete text in password field emidiatelly
        self.password.setText('')

        self.login_btn.setEnabled(False)
        self.login.emit(self.report_error, usr, psw)

    def report_error(self, message):
        self.login_btn.setEnabled(True)
        self.error_reporter.setText(message)


class RegisterPage(QWidget):

    on_register = pyqtSignal(object, str, str, str)
    action_chosen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        outer_container = QWidget()
        self.email = QLineEdit()
        self.email.setPlaceholderText('Email')
        self.email.setFixedSize(300, 25)
        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setFixedSize(300, 25)
        self.password = QLineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setFixedSize(300, 25)
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText('Confirm Password')
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setFixedSize(300, 25)
        self.error_reporter = QLabel()
        self.error_reporter.setStyleSheet('color: red;')
        self.error_reporter.setFixedSize(300, 25)
        self.register_btn = QPushButton('Register')
        self.register_btn.clicked.connect(self.emit)
        self.register_btn.setFixedSize(100, 30)
        self.back_btn = QPushButton('Back')
        self.back_btn.clicked.connect(lambda: self.action_chosen.emit(0))
        self.back_btn.setFixedSize(100, 30)

        mlayout = QVBoxLayout()
        mlayout.setAlignment(Qt.AlignCenter)
        mlayout.addWidget(outer_container)

        layout = QVBoxLayout()
        layout.addWidget(self.email, 0, Qt.AlignCenter)
        layout.addWidget(self.username, 0, Qt.AlignCenter)
        layout.addWidget(self.password, 0, Qt.AlignCenter)
        layout.addWidget(self.confirm_password, 0, Qt.AlignCenter)
        layout.addWidget(self.error_reporter, 0, Qt.AlignCenter)
        layout.insertSpacing(5, 20)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.register_btn)
        layout.addLayout(btn_layout)

        outer_container.setLayout(layout)
        self.setLayout(mlayout)

    def emit(self):
        email = self.email.text()
        usr = self.username.text()
        psw = self.password.text()
        confirm = self.confirm_password.text()

        if len(psw) < 1:
            self.error_reporter.setText("Password field can't be empty.")
            return

        if EMAIL_REGEX.match(email) is None:
            self.error_reporter.setText('Invalid email !')
            return

        if psw != confirm:
            self.error_reporter.setText("Passwords do not mach !")
            return

        self.password.setText('')
        self.confirm_password.setText('')

        self.register_btn.setEnabled(False)
        self.on_register.emit(self.report_error, email, usr, psw)

    def report_error(self, message):
        self.register_btn.setEnabled(True)
        self.error_reporter.setText(message)
