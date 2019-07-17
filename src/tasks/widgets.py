from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QWidget, QCheckBox, QMenu, QToolButton, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QRect
from tasks.objects import create_task_object, TaskObject


class AddTaskDialog(QDialog):

    accepted = pyqtSignal(TaskObject)
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
        task = create_task_object(description)

        self.accepted.emit(task)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class EditTaskDialog(QDialog):
    accepted = pyqtSignal(object)
    rejected = pyqtSignal(bool)

    def __init__(self, task_object, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

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

        self.accepted.emit(task)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class TaskWidget(QFrame):

    on_remove = pyqtSignal(str)
    on_review = pyqtSignal(str)

    def __init__(self, text, actions, icon=None, max_text_width=200, parent=None):
        super().__init__(parent)
        self.actions = actions
        self.setObjectName("TaskWidget")

        # self.setStyleSheet("")
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFixedWidth(max_text_width)
        if icon:
            self.icon = QToolButton()
            self.icon.setIcon(icon)
            self.icon.setMaximumSize(20, 20)
            self.icon.setAutoRaise(True)

        self.checker = None

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        if icon:
            self.layout.addWidget(self.icon)
        self.layout.addStretch(0)
        self.setLayout(self.layout)

        # Event can't be passed to parent if task widget is not set to receive move events
        self.setMouseTracking(True)
        self._animating_enter = False
        self._animating_leave = False

        self.on_mouseover_anim = QPropertyAnimation(self, b"geometry")
        self.on_mouseover_anim.setDuration(100)
        self.on_mouseover_anim.finished.connect(self._enter_animation_done)

        self.on_mouseleave_anim = QPropertyAnimation(self, b"geometry")
        self.on_mouseleave_anim.setDuration(100)
        self.on_mouseleave_anim.finished.connect(self._leave_animation_done)

        self.start_pos = None
        self.diff = 5

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

    def enterEvent(self, event):
        print("TASK ENTER")
        if self._animating_enter:
            return

        self._animating_leave = False
        self._animating_enter = True
        self.start_pos = QRect(self.x(), self.y(), self.width(), self.height())
        end_pos = QRect(self.start_pos.x(), self.start_pos.y() - self.diff, self.width(), self.height())
        print('>>>', self.start_pos, end_pos)
        self.on_mouseover_anim.setStartValue(self.start_pos)
        self.on_mouseover_anim.setEndValue(end_pos)
        self.on_mouseover_anim.start()

    def leaveEvent(self, event):
        print("TASK LEAVE", self.on_mouseover_anim.currentTime())
        if self._animating_leave:
            return

        if (self.y() + self.diff) < 0 or (self.y() + self.diff) > self.parent().height():
            print("SHIT IT'S LESS THAN 0")
            start_pos = QRect(self.x(), self.y(), self.width(), self.height())
            end_pos = QRect(self.x(), self.y() + self.diff, self.width(), self.height())
        else:
            start_pos = self.on_mouseover_anim.currentValue()
            end_pos = QRect(self.start_pos)
        print("startpos, endpos:", start_pos, end_pos)

        self._animating_enter = False
        self._animating_leave = True
        # start_pos = QRect(self.x(), self.y(), self.width(), self.height())
        # end_pos = QRect(start_pos.x(), start_pos.y() + self.diff, self.width(), self.height())
        self.on_mouseleave_anim.setStartValue(start_pos)
        self.on_mouseleave_anim.setEndValue(end_pos)
        self.on_mouseleave_anim.start()

    def _enter_animation_done(self):
        print("Enter animation done !")
        self._animating_enter = False

    def _leave_animation_done(self):
        print("Leave animation done !")
        self._animating_leave = False
