from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QGroupBox, QDialog, QTextEdit, QLineEdit, QWidget, QSizePolicy, \
    QListWidget, QListWidgetItem, QListView, QAbstractItemView, QApplication, \
    QToolButton, QCheckBox
from PyQt5.QtCore import pyqtSignal, QSize, Qt


class CustomListWidget(QListWidget):

    dropped = pyqtSignal(int)
    dragstarted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.setStyleSheet('background: #FFAA22;')

    def update_drag(self, index):
        self.drag_index = index

    def move_items(self, drop_index):
        self.storage.move_task_by_index(self.name, self.drag_index, drop_index)

    def load(self):
        size = QSize()
        size.setHeight(50)
        for task in self.storage.tasks(self.name):
            widget = TaskWidget(task[0])

            item = QListWidgetItem()
            item.setSizeHint(size)

            self.lw.addItem(item)
            self.lw.setItemWidget(item, widget)

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
        item.setSizeHint(50)
        self.lw.addItem(item)
        self.lw.setItemWidget(item, widget)

    def set_multi_selection(self):
        self.lw.clearSelection()
        self.lw.setSelectionMode(QAbstractItemView.MultiSelection)
        # Have to turn off drag and drop for multi-selection because currently
        # storage doesn't support multiple drags and drops of items.
        self.lw.setDragDropMode(QAbstractItemView.NoDragDrop)

    def set_single_selection(self):
        self.lw.clearSelection()
        self.lw.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lw.setDragDropMode(QAbstractItemView.InternalMove)

    def remove_selected_item(self):
        current_item = self.lw.currentItem()
        if current_item is None:
            return

        index = self.lw.currentIndex().row()
        self.storage.remove_task_by_index(self.name, index)
        self.lw.takeItem(index)

    def get_selected_rows(self):
        selected_rows = [i.row() for i in self.lw.selectedIndexes()]
        selected_rows.sort(reverse=True)
        return selected_rows

    def remove_selected_items(self):
        rows = self.get_selected_rows()
        print(rows)
        for index in rows:
            self.storage.remove_task_by_index(self.name, index)
            self.lw.takeItem(index)


class QueueActions(QWidget):

    def __init__(self, queue_widget=None, parent=None):
        super().__init__(parent)

        self.queue_widget = queue_widget
        self.selection_flag = False

        mlayout = QVBoxLayout()

        self.add_task_btn = QPushButton('Add Task')
        self.add_task_btn.clicked.connect(self.run_add_task_dialog)
        # Connect to remove_task.clicked for signals
        self.remove_task_btn = QPushButton('Remove Task')
        self.remove_task_btn.clicked.connect(self.remove_task)
        self.select_tasks = QPushButton('Select Tasks')
        self.select_tasks.clicked.connect(self.toggle_selection)

        self.select_on_stylesheet = 'background: green; border: 1px solid red; padding: 2px;'
        self.select_off_stylesheet = ''

        mlayout.addWidget(self.add_task_btn)
        mlayout.addWidget(self.remove_task_btn)
        mlayout.addWidget(self.select_tasks)
        self.setLayout(mlayout)

    def set_queue_widget(self, queue_widget):
        self.queue_widget = queue_widget

    def run_add_task_dialog(self):
        dialog = AddTaskDialog(self.queue_widget.task_names())
        dialog.accepted.connect(self.queue_widget.add)
        dialog.exec_()

    def remove_task(self):
        if self.selection_flag:
            self.queue_widget.remove_selected_items()
        else:
            self.queue_widget.remove_selected_item()

    def toggle_selection(self):
        self.selection_flag = not self.selection_flag

        if self.selection_flag:
            self.add_task_btn.setDisabled(True)
            self.queue_widget.set_multi_selection()
            self.select_tasks.setStyleSheet(self.select_on_stylesheet)
        else:
            self.add_task_btn.setEnabled(True)
            self.queue_widget.set_single_selection()
            self.select_tasks.setStyleSheet(self.select_off_stylesheet)


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



class QueueManager(QWidget):

    def __init__(self, sidebar, storage, parent=None):
        super().__init__(parent)

        mlayout = QHBoxLayout()

        self.layout = QVBoxLayout()
        mlayout.addLayout(self.layout)

        self.qa = QueueActions()
        self.qa.hide()
        mlayout.addWidget(self.qa)

        self.setLayout(mlayout)

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.display_queue)
        self.storage = storage
        self.cq = None  # current queue

    def display_queue(self, name):
        if not self.cq:
            self.cq = QueueWidget(name, self.storage)
            self.qa.show()
        elif self.cq.name != name:
            self.layout.removeWidget(self.cq)
            self.cq.deleteLater()
            self.cq = QueueWidget(name, self.storage)
        else:
            return

        self.qa.set_queue_widget(self.cq)
        self.layout.addWidget(self.cq)
        self.cq.load()


class TaskWidget(QWidget):

    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.label = QLabel(text)
        self.rmbtn = QToolButton()
        self.rmbtn.setText('X')
        self.rmbtn.setFixedSize(20, 20)

        self.checker = None

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.rmbtn)

        self.setLayout(self.layout)

    def add_checker(self):
        self.checker = QCheckBox()
        self.layout.insertWidget(0, self.checker)
