from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QCheckBox, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPalette

from widgets import Sidebar, SidebarButton

import time


class CustomListWidget(QListWidget):
    dragstarted = pyqtSignal(str, int)
    internal_drop = pyqtSignal(int)
    external_drop = pyqtSignal(int, str)

    def __init__(self, name, parent=None):
        super().__init__(parent)

        self.name = name
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def dropEvent(self, event):
        super().dropEvent(event)
        dropped_at_item = self.itemAt(event.pos())
        new_item_pos = self.indexFromItem(dropped_at_item).row()

        drop_indicator = self.dropIndicatorPosition()
        if event.source() == self:
            if drop_indicator == 1:
                new_item_pos -= 1
            elif drop_indicator == 3:
                new_item_pos = self.count() - 1

            self.internal_drop.emit(new_item_pos)
        else:
            if drop_indicator == 2:
                new_item_pos += 1
            elif drop_indicator == 3:
                new_item_pos = self.count() - 1

            self.external_drop.emit(new_item_pos, event.mimeData().text())

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        source = event.source()
        if isinstance(source, type(self)):
            event.accept()
        if source == self:
            widget = self.itemWidget(self.item(self.currentIndex().row()))
            event.mimeData().setText(widget.label.text())

        self.dragstarted.emit(source.name, source.currentIndex().row())


class QueueWidget(QWidget):

    def __init__(self, name, storage, parent=None):
        super().__init__(parent)

        self.name = name
        self.storage = storage

        self.drag_source = ''
        self.drag_index = 0

        self.lw = CustomListWidget(name, self)
        self.lw.dragstarted.connect(self.update_drag)
        self.lw.internal_drop.connect(self.move_item)
        self.lw.external_drop.connect(self.handle_external_drop)
        self.lw.setDragDropMode(QAbstractItemView.DragDrop) #InternalMove
        self.lw.setDefaultDropAction(Qt.MoveAction)
        self.lw.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lw)
        self.setLayout(layout)

    def update_drag(self, source_name, index):
        self.drag_source = source_name
        self.drag_index = index

    def handle_external_drop(self, drop_index, task_text):
        item = self.lw.item(drop_index)
        task = TaskWidget(task_text)
        task.on_remove.connect(self.remove_task)
        self.lw.setItemWidget(item, task)
        self.migrate_item(drop_index)

    def move_item(self, drop_index):
        print('Moving item:', self.name, self.drag_index, drop_index)
        self.storage.move_task_by_index(self.name, self.drag_index, drop_index)

    def migrate_item(self, drop_index):
        print('Migrating item:', self.name, self.drag_source, self.drag_index, drop_index)
        task = self.storage.pop_task(self.drag_source, self.drag_index)
        print('Migrated Task:', task)
        self.storage.insert_task(self.name, task, drop_index)

    def load(self):
        t1 = time.perf_counter()
        size = QSize()
        size.setHeight(50)
        delete_icon = QIcon()
        delete_icon.addPixmap(QPixmap(':/images/delete_icon2.png'))
        for task in self.storage.tasks(self.name):
            widget = TaskWidget(task[0], delete_icon)
            widget.on_remove.connect(self.remove_task)

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

    def remove_task(self, name):
        task_index = self.storage.find_task(self.name, name)
        self.lw.takeItem(task_index)
        self.storage.remove_task_by_index(self.name, task_index)

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
        for index in range(len(rows) - 1, -1, -1):
            self.lw.takeItem(rows[index])
            self.storage.remove_task_by_index(self.name, rows[index])

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

        self.qname_lbl = QLabel(queue_widget.name)

        self.select = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/select_icon.png'))
        self.select.setIcon(icon)
        self.select.setMaximumSize(20, 20)
        self.select.setAutoRaise(True)
        self.select.clicked.connect(self.selection_triggered)

        self.delete = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/delete_icon.png'))
        self.delete.setIcon(icon)
        self.delete.setMaximumSize(20, 20)
        self.delete.setAutoRaise(True)
        self.delete.clicked.connect(self.delete_triggered)

        self.add = QToolButton(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(':/images/add_icon.png'))
        self.add.setIcon(icon)
        self.add.setMaximumSize(20, 20)
        self.add.setAutoRaise(True)
        self.add.clicked.connect(self.run_add_task_dialog)

        layout = QHBoxLayout(self)
        # Set spacing and margins instead of widget size
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        ###
        layout.addWidget(self.qname_lbl)
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
        self.sidebar.itemclicked.connect(self.display_or_remove)
        self.sidebar.itemremoved.connect(self.remove_if_exists)
        self.storage = storage
        self.cq = None  # current queue
        self.queues = {}

        self.queuelayout = QHBoxLayout()
        self.setLayout(self.queuelayout)

    def display_or_remove(self, queue_name):
        if queue_name in self.queues:
            self.remove_queue(queue_name)
        else:
            self.display_queue(queue_name)

    def remove_if_exists(self, queue_name):
        if queue_name in self.queues:
            self.remove_queue(queue_name)

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

    on_remove = pyqtSignal(str)

    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)

        # creating icon every time is proximately 3 times slower than creating it once
        # and passing it many times
        if not icon:
            icon = QIcon()
            icon.addPixmap(QPixmap(':/images/delete_icon.png'))

        self.label = QLabel(text)
        self.rmbtn = QToolButton()
        self.rmbtn.setIcon(icon)
        self.rmbtn.setIconSize(QSize(25, 25))
        self.rmbtn.setIcon(icon)
        self.rmbtn.setFixedSize(20, 20)
        self.rmbtn.setAutoRaise(True)
        self.rmbtn.clicked.connect(lambda: self.on_remove.emit(text))

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


class QueueSidebar(QWidget):

    itemclicked = pyqtSignal(str)
    itemremoved = pyqtSignal(str)

    def __init__(self, storage, parent=None):
        super().__init__(parent)

        self.storage = storage
        self.sidebar = Sidebar(parent=self)
        self.sidebar.itemclicked.connect(self.handle_item_clicked)

        self.add_queue_btn = QToolButton()
        self.add_queue_btn.setIcon(QIcon(QPixmap(':/images/add_icon.png')))
        self.add_queue_btn.setIconSize(QSize(30, 30))
        self.add_queue_btn.setAutoRaise(True)
        self.add_queue_btn.clicked.connect(self.run_dialog)

        self.remove_mode_flag = False
        self.remove_queue_btn = QToolButton()
        self.remove_queue_btn.setIcon(QIcon(QPixmap(':/images/delete_icon.png')))
        self.remove_queue_btn.setIconSize(QSize(30, 30))
        self.remove_queue_btn.setAutoRaise(True)
        self.remove_queue_btn.clicked.connect(self.toggle_remove_mode)


        mlayout = QHBoxLayout()
        mlayout.addWidget(self.sidebar)
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.add_queue_btn)
        btn_layout.addWidget(self.remove_queue_btn)
        mlayout.addLayout(btn_layout)
        self.setLayout(mlayout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

    def add_widget(self, widget, name):
        self.sidebar.add_widget(widget, name)

    def handle_item_clicked(self, name):
        if self.remove_mode_flag:
            self.sidebar.remove_widget(name)
            self.storage.remove_queue(name)
            self.itemremoved.emit(name)
        else:
            self.itemclicked.emit(name)

    def run_dialog(self):
        add_queue_dialog = AddQueueDialog(self.storage.queues())
        add_queue_dialog.accepted.connect(self.add_queue)
        add_queue_dialog.exec_()

    def add_queue(self, name):
        print('Adding:', name)
        self.storage.add_queue(name)
        widget = SidebarButton(name)
        widget.setFixedSize(80, 20)
        self.sidebar.add_widget(widget, name)

    def toggle_remove_mode(self):
        self.remove_mode_flag = not self.remove_mode_flag
        if self.remove_mode_flag:
            self.add_queue_btn.setDisabled(True)
        else:
            self.add_queue_btn.setEnabled(True)

    def mousePressEvent(self, event):
        # If click was on child, don't change color
        if self.childAt(event.pos()):
            super().mousePressEvent(event)
            return
        pal = QPalette()
        pal.setColor(QPalette.Window, Qt.yellow)
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def mouseDoubleClickEvent(self, event):
        # Don't call super() because for some reason it won't set the palette.
        self.setPalette(self.parent().palette())


class AddQueueDialog(QDialog):

    accepted = pyqtSignal(str)
    rejected = pyqtSignal(bool)

    def __init__(self, queue_names, parent=None):
        super().__init__(parent)

        self.queue_names = queue_names

        self.qname = QLineEdit(self)
        self.qname.setPlaceholderText('Queue Name')
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.qname)
        mlayout.addLayout(btn_layout)
        self.setLayout(mlayout)

    def accept(self):
        queue_name = self.qname.text()
        if queue_name in self.queue_names:
            self.qname.setStyleSheet('border: 1px solid red;')
            return

        self.accepted.emit(queue_name)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()
