from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QCheckBox, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPalette

import time


class CustomListWidget(QListWidget):

    dropped = pyqtSignal(int)
    dragstarted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def dropEvent(self, event):
        super().dropEvent(event)
        # You must check currentIndex after the drop event has been processed
        self.dropped.emit(self.currentIndex().row())

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        self.dragstarted.emit(self.currentIndex().row())


class QueueWidget(QWidget):

    def __init__(self, name, storage, parent=None):
        super().__init__(parent)

        self.name = name
        self.storage = storage
        self.drag_index = 0

        self.lw = CustomListWidget(self)
        self.lw.dragstarted.connect(self.update_drag)
        self.lw.dropped.connect(self.move_items)
        self.lw.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lw)
        self.setLayout(layout)

    def update_drag(self, index):
        self.drag_index = index

    def move_items(self, drop_index):
        self.storage.move_task_by_index(self.name, self.drag_index, drop_index)

    def load(self):
        t1 = time.perf_counter()
        size = QSize()
        size.setHeight(50)
        delete_icon = QIcon()
        delete_icon.addPixmap(QPixmap(':/images/delete_icon.png'))
        for task in self.storage.tasks(self.name):
            widget = TaskWidget(task[0], delete_icon)

            item = QListWidgetItem()
            item.setSizeHint(size)

            self.lw.addItem(item)
            self.lw.setItemWidget(item, widget)

        t2 = time.perf_counter()
        print('Time took for loading {} items: {}'.format(self.lw.count(), t2 - t1))

    def task_names(self):
        return self.storage.task_names(self.name)

    def remove(self, index):
        self.storage.remove_task_by_index(self.name, index)

    def add(self, task):
        print('Adding new task')
        name, value = task

        if name in self.storage.task_names(self.name):
            print('This task already exists')
            return

        self.storage.add_task(self.name, name, value)

        widget = TaskWidget(task[0])
        item = QListWidgetItem()
        size = QSize()
        size.setHeight(50)
        item.setSizeHint(size)
        self.lw.addItem(item)
        self.lw.setItemWidget(item, widget)

    def get_selected_rows(self):
        num_items = self.lw.count()
        selected_rows = []
        for idx in range(num_items):
            widget = self.lw.itemWidget(self.lw.item(idx))
            if widget.checker.isChecked():
                selected_rows.append(idx)
        return selected_rows

    def remove_selected_items(self):
        rows = self.get_selected_rows()
        print(rows)
        for index in range(len(rows) - 1, -1, -1):
            self.storage.remove_task_by_index(self.name, rows[index])
            self.lw.takeItem(rows[index])

    def turn_on_selection(self):
        items = self.lw.count()
        for idx in range(items):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.add_checker()

    def turn_off_selection(self):
        num_items = self.lw.count()
        for idx in range(num_items):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.remove_checker()


class AddTaskDialog(QDialog):

    accepted = pyqtSignal(list)
    rejected = pyqtSignal(bool)

    def __init__(self, task_list, parent=None):
        super().__init__(parent)

        self._task_list = task_list

        mlayout = QVBoxLayout()
        namelayout = QHBoxLayout()
        desclayout = QHBoxLayout()
        stimelayout = QHBoxLayout()
        etimelayout = QHBoxLayout()
        btnslayout = QHBoxLayout()

        namelbl = QLabel('Task Name:', self)
        self.name_line_edit = QLineEdit(self)
        namelayout.addWidget(namelbl)
        namelayout.addWidget(self.name_line_edit)

        desclbl = QLabel('Description:', self)
        self.desc_text_edit = QTextEdit(self)
        desclayout.addWidget(desclbl)
        desclayout.addWidget(self.desc_text_edit)

        stimelbl = QLabel('Start Time:', self)
        self.stime_line_edit = QLineEdit(self)
        stimelayout.addWidget(stimelbl)
        stimelayout.addWidget(self.stime_line_edit)

        etimelbl = QLabel('Start Time:', self)
        self.etime_line_edit = QLineEdit(self)
        etimelayout.addWidget(etimelbl)
        etimelayout.addWidget(self.etime_line_edit)

        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        btnslayout.addWidget(self.ok_btn)
        btnslayout.addWidget(self.cancel_btn)

        mlayout.addLayout(namelayout)
        mlayout.addLayout(desclayout)
        mlayout.addLayout(stimelayout)
        mlayout.addLayout(etimelayout)
        mlayout.addLayout(btnslayout)

        self.setLayout(mlayout)

    def accept(self):
        task_name = self.name_line_edit.text()
        if task_name in self._task_list:
            self.name_line_edit.setStyleSheet('border: 1px solid red;')
            return
        description = self.desc_text_edit.toPlainText()
        start_time = round(float(self.stime_line_edit.text()), 2)
        end_time = round(float(self.etime_line_edit.text()), 2)

        if not (0.00 <= start_time <= 24.00):
            self.stime_line_edit.setStyleSheet('border: 1px solid red;')
            return
        if not (0.00 <= end_time <= 24.00):
            self.etime_line_edit.setStyleSheet('border: 1px solid red;')
            return

        task = [task_name, {'description': description, 'start_time': start_time, 'end_time': end_time}]

        self.accepted.emit(task)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class QueueActions(QWidget):

    def __init__(self, queue_widget=None, parent=None):
        super().__init__(parent)

        self.queue_widget = queue_widget
        self.selection_flag = False

        self.select = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/delete_icon2.png'))
        self.select.setIcon(icon)
        self.select.setMaximumSize(20, 20)
        self.select.clicked.connect(self.selection_triggered)

        self.delete = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/delete_icon2.png'))
        self.delete.setIcon(icon)
        self.delete.setMaximumSize(20, 20)
        self.delete.clicked.connect(self.delete_triggered)

        self.add = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/delete_icon2.png'))
        self.add.setIcon(icon)
        self.add.setMaximumSize(20, 20)
        self.add.clicked.connect(self.run_add_task_dialog)

        layout = QHBoxLayout(self)
        # Set spacing and margins instead of widget size
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        ###
        layout.addStretch(1)
        layout.addWidget(self.select)
        layout.addWidget(self.delete)
        layout.addWidget(self.add)
        layout.addStretch(1)
        self.setLayout(layout)

    def selection_triggered(self):
        if not self.selection_flag:
            self.queue_widget.turn_on_selection()
            self.selection_flag = True
            self.add.setDisabled(True)
        else:
            self.queue_widget.turn_off_selection()
            self.selection_flag = False
            self.add.setEnabled(True)

    def delete_triggered(self):
        if self.selection_flag:
            self.queue_widget.remove_selected_items()

    def run_add_task_dialog(self):
        dialog = AddTaskDialog(self.queue_widget.task_names())
        dialog.accepted.connect(self.queue_widget.add)
        dialog.exec_()



class QueueManager(QWidget):

    def __init__(self, sidebar, storage, parent=None):
        super().__init__(parent)

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.check_existance)
        self.storage = storage
        self.cq = None  # current queue
        self.queues = {}

        self.queuelayout = QHBoxLayout()
        self.setLayout(self.queuelayout)

    def check_existance(self, queue_name):
        if queue_name in self.queues:
            self.remove_queue(queue_name)
        else:
            self.display_queue(queue_name)

    def display_queue(self, name):
        container = QWidget(self)
        queue_widget = QueueWidget(name, self.storage, container)
        queue_actions = QueueActions(queue_widget, container)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(queue_actions)
        layout.addWidget(queue_widget)
        container.setLayout(layout)
        container.setMaximumWidth(300)

        self.queues[name] = container
        self.queuelayout.addWidget(container)
        queue_widget.load()

    def remove_queue(self, name):
        container = self.queues[name]
        self.queuelayout.removeWidget(container)
        container.deleteLater()
        self.queues.pop(name)


class TaskWidget(QWidget):

    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)

        # creating icon every time is proximately 3 times slower than creating it once
        # and passing it many times
        if not icon:
            icon = QIcon(":/images/delete_icon.png")

        self.label = QLabel(text)
        self.rmbtn = QToolButton()
        self.rmbtn.setIcon(icon)
        self.rmbtn.setIconSize(QSize(25, 25))
        self.rmbtn.setIcon(icon)
        self.rmbtn.setFixedSize(25, 25)
        self.rmbtn.setAutoRaise(True)

        self.checker = None

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.rmbtn)

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