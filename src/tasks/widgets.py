from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QCheckBox, QSizePolicy, QApplication, \
    QMenu
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from resources.manager import resource
from tasks.objects import create_task_object, TaskObject


class AddTaskDialog(QDialog):

    accepted = pyqtSignal(TaskObject)
    rejected = pyqtSignal(bool)

    def __init__(self, tasks_descriptions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create new task")

        self._tasks_descriptions = tasks_descriptions

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
        if description in self._tasks_descriptions:
            self.desc_text_edit.setStyleSheet('border: 1px solid red;')
            return

        task = create_task_object(description)

        self.accepted.emit(task)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class ReviewTaskDialog(QDialog):
    accepted = pyqtSignal(dict, dict)
    rejected = pyqtSignal(bool)

    def __init__(self, task_object, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Task")

        self.old_task = task_object

        mlayout = QVBoxLayout()
        desclayout = QHBoxLayout()
        btnslayout = QHBoxLayout()

        desclbl = QLabel('Description:', self)
        self.desc_text_edit = QTextEdit(self)
        self.desc_text_edit.setMaximumHeight(100)
        self.desc_text_edit.setPlainText(self.old_task.description)
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
        description = self.desc_text_edit.toPlainText()
        task = create_task_object(description)

        self.accepted.emit(self.old_task, task)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class TaskWidget(QWidget):

    on_remove = pyqtSignal(str)
    on_review = pyqtSignal(str)

    def __init__(self, text, actions, max_text_width=200, parent=None):
        super().__init__(parent)
        self.actions = actions

        self.label = QLabel(text)
        self.label.setMaximumWidth(max_text_width)

        self.checker = None

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
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

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() != Qt.RightButton:
            return

        action_menu = QMenu()
        action_map = {}
        for action in self.actions:
            a = action_menu.addAction(action.icon, action.text)
            action_map[a] = action

        chosen_action = action_menu.exec_(self.mapToGlobal(event.pos()))
        action_map[chosen_action].signal.emit(self.label.text())
