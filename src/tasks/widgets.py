from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QWidget, QCheckBox, QMenu, QToolButton, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QPalette, QColor

import datetime


class AddTaskDialog(QDialog):

    accepted = pyqtSignal(str)
    rejected = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create new task")

        mlayout = QVBoxLayout()
        desclayout = QVBoxLayout()
        btnslayout = QHBoxLayout()

        desclbl = QLabel('Description:', self)
        self.desc_text_edit = QTextEdit(self)
        self.desc_text_edit.setMaximumHeight(100)
        desclayout.addWidget(desclbl)
        desclayout.addWidget(self.desc_text_edit)

        self.ok_btn = QPushButton('OK')
        self.ok_btn.setMaximumWidth(100)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setMaximumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)

        btnslayout.addWidget(self.ok_btn)
        btnslayout.addWidget(self.cancel_btn)
        btnslayout.setContentsMargins(0, 20, 0, 0)

        mlayout.addLayout(desclayout)
        mlayout.addLayout(btnslayout)
        self.setLayout(mlayout)

    def accept(self):
        description = self.desc_text_edit.toPlainText()

        self.accepted.emit(description)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class EditTaskDialog(QDialog):
    accepted = pyqtSignal(str, int)
    rejected = pyqtSignal(bool)

    def __init__(self, task_description, created_at, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

        self.task_desc = task_description
        self.created = created_at

        mlayout = QVBoxLayout()
        desclayout = QHBoxLayout()
        btnslayout = QHBoxLayout()

        desclbl = QLabel('Description:', self)
        self.desc_text_edit = QTextEdit(self)
        self.desc_text_edit.setMaximumHeight(100)
        self.desc_text_edit.setPlainText(self.task_desc)
        desclayout.addWidget(desclbl)
        desclayout.addWidget(self.desc_text_edit)

        self.ok_btn = QPushButton('OK')
        self.ok_btn.setMaximumWidth(100)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setMaximumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)

        btnslayout.addWidget(self.ok_btn)
        btnslayout.addWidget(self.cancel_btn)
        btnslayout.setContentsMargins(0, 30, 0, 0)

        mlayout.addLayout(desclayout)
        mlayout.addLayout(btnslayout)
        self.setLayout(mlayout)

    def accept(self):
        new_description = self.desc_text_edit.toPlainText()
        now = datetime.datetime.now().timestamp()
        self.created = int(now)

        self.accepted.emit(new_description, self.created)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class TaskWidget(QWidget):

    on_remove = pyqtSignal(int)
    on_review = pyqtSignal(int)

    def __init__(self, rid, text, actions, icon=None, max_text_width=200, parent=None):
        super().__init__(parent)
        self.rid = rid
        self.actions = actions
        self.setObjectName("TaskWidget")

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFixedWidth(max_text_width)
        if icon:
            self.icon_btn = QToolButton()
            self.icon_btn.setIcon(icon)
            self.icon_btn.setMaximumSize(20, 20)
            self.icon_btn.setAutoRaise(True)
        else:
            self.icon_btn = None

        self.checker = None

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        if icon:
            self.layout.addWidget(self.icon_btn)
        self.layout.addStretch(0)
        self.setLayout(self.layout)

    def add_checker(self):
        # if checker is present just return
        if self.checker:
            return

        self.checker = QCheckBox()
        self.layout.insertWidget(0, self.checker)

    def remove_checker(self):
        self.layout.removeWidget(self.checker)
        self.checker.deleteLater()
        self.checker = None

    def set_text(self, text):
        self.label.setText(text)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() != Qt.RightButton:
            return
        action_menu = QMenu()
        action_map = {}
        for action in self.actions:
            if action.icon is None:
                a = action_menu.addAction(action.text)
            else:
                a = action_menu.addAction(action.icon, action.text)
            action_map[a] = action

        chosen_action = action_menu.exec_(self.mapToGlobal(event.pos()))
        if chosen_action is None:
            return
        action_map[chosen_action].signal.emit(self.mapToGlobal(event.pos()))
