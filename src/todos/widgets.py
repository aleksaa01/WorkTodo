from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QTextEdit, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QCheckBox, QSizePolicy, QApplication, \
    QMenu, QScrollArea
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QPainter

from widgets import Sidebar, SidebarButton
from tasks.widgets import AddTaskDialog, ReviewTaskDialog, TaskWidget
from tasks.objects import TaskObject
from tasks.models import TasksModel
from tasks.actions import Action
from resources.manager import resource

import time


class CustomListWidgetManager(QScrollArea):

    def __init__(self, model, sidebar, parent=None):
        super().__init__(parent)

        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.setFixedSize(500, 500)

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.display_or_remove)

        self.mwidget = QWidget()
        self.mlayout = QHBoxLayout()
        self.mwidget.setLayout(self.mlayout)
        self.setWidget(self.mwidget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)

        # TODO: Rename to self._todo_mapper
        self._mapper = {}
        self._model = model

        self.drag_index = None
        self.drag_source = None
        self.drop_index = None
        self.drop_source = None

    def set_model(self, model):
        self._model = model

    def display_or_remove(self, todo_name):
        if todo_name in self._mapper:
            self.remove_todo(todo_name)
        else:
            self.display_todo(todo_name)

    def remove_if_exists(self, todo_name):
        if todo_name in self._mapper:
            self.remove_todo(todo_name)

    def remove_todo(self, todo_name):
        todo_widget = self._mapper[todo_name]
        self.mlayout.removeWidget(todo_widget)
        # FIXME: Deleting a parent seems like a weird thing to do,
        #   but having container complicates things, because you now
        #   you have to get a todo_widget from a container somehow or
        #   you have to store containers too. Just make a new widget that
        #   will hold both todo_widget and todo_actions.
        todo_widget.parent().deleteLater()
        self._mapper.pop(todo_name)

    def display_todo(self, todo_name):
        container = QWidget(self)
        todo_widget = CustomTodoWidget(todo_name, container)
        todo_widget.drag_event.connect(self.update_drag)
        todo_widget.drop_event.connect(self.update_drop)
        todo_actions = TodoActions(todo_widget, container)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(todo_actions)
        layout.addWidget(todo_widget)
        container.setLayout(layout)
        container.setFixedWidth(300)

        self._mapper[todo_name] = todo_widget
        self.mlayout.addWidget(container)
        todo_widget.load()

    def update_drag(self, todo_name, index):
        self.drag_source = self._mapper[todo_name]
        self.drag_index = index

    def update_drop(self, todo_name, drop_index, indicator):
        drop_source = self._mapper[todo_name]
        if self.drag_source == drop_source:
            drop_index = self._fix_drop_offset(drop_index, indicator)

        task_object = self.drag_source.pop_task(self.drag_index)
        drop_source.insert_task(drop_index, task_object)

    def _fix_drop_offset(self, drop_index, indicator):
        if self.drag_index < drop_index:
            if indicator == 1:
                drop_index -= 1
        elif self.drag_index > drop_index:
            if indicator == 2:
                drop_index += 1
        return drop_index


class CustomTodoWidget(QWidget):
    drag_event = pyqtSignal(str, int)
    drop_event = pyqtSignal(str, int, int)

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name

        self.lw = NewCustomListWidget(self)
        self.lw.drag_event.connect(self.emit_drag_event)
        self.lw.drop_event.connect(self.emit_drop_event)
        self.lw.setDragDropMode(QAbstractItemView.DragDrop)  # InternalMove
        # You don't have to remove items yourself if you use MoveAction
        self.lw.setDefaultDropAction(Qt.MoveAction)
        self.lw.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lw)
        self.setLayout(layout)

        self.model = TasksModel(self.name)

    def emit_drag_event(self, index):
        print('Drag emmited >>> ', index)
        self.drag_event.emit(self.name, index)

    def emit_drop_event(self, index, indicator):
        print('Drop emmited >>> ', index)
        self.drop_event.emit(self.name, index, indicator)

    def load(self):
        print('Loading data...')
        t1 = time.perf_counter()

        action_remove = Action('Remove', resource.get_icon('delete_icon'))
        action_remove.signal.connect(self.find_and_remove)
        # action_review = Action('Review')
        # action_review.signal.connect(self.find_and_remove)
        self.actions = [action_remove]
        for task_object in self.model.tasks():
            task_widget = TaskWidget(task_object.description, self.actions)
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.lw.addItem(item)
            self.lw.setItemWidget(item, task_widget)
            QApplication.processEvents()
        t2 = time.perf_counter()
        print('Time took:', t2 - t1)

    def get_task(self, index):
        return self.model.get_task(index)

    def pop_task(self, index):
        item = self.lw.takeItem(index)
        del item
        return self.model.pop_task(index)

    def find_and_remove(self, text):
        idx = self.model.find_task(text)
        assert idx != -1  # fail if task wasn't found
        print('idx >>>', idx)
        self.pop_task(idx)

    def insert_task(self, index, task_object):
        # WARNING: Maybe we should first delete TaskWidget at the index, before
        #   we create new one and do a setItemWidget.
        task_widget = TaskWidget(task_object.description, self.actions)
        item = QListWidgetItem()
        item.setSizeHint(task_widget.sizeHint())
        self.lw.insertItem(index, item)
        self.lw.setItemWidget(item, task_widget)
        self.model.insert_task(index, task_object)
        self._sanity_check()

    def _sanity_check(self):
        for idx, task in enumerate(self.model.tasks()):
            widget = self.lw.itemWidget(self.lw.item(idx))
            if widget.label.text() == task.description:
                continue
            print('ALERT ! ALERT !  MODEL AND VIEW ARE OUT OF SYNC')
            print('MODEL, ITEMS: ', [i.description for i in self.model.tasks()], [self.lw.itemWidget(self.lw.item(i)).label.text() for i in range(len(self.model.tasks()))])

    def turn_on_selection(self):
        for idx in range(len(self.model)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.add_checker()

    def turn_off_selection(self):
        for idx in range(len(self.model)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.remove_checker()

    def remove_selected_items(self):
        selected_rows = self.get_selected_rows()
        for idx in range(len(selected_rows) - 1, -1, -1):
            self.pop_task(selected_rows[idx])

    def get_selected_rows(self):
        selected_rows = []
        for idx in range(len(self.model)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            if widget.checker.isChecked():
                selected_rows.append(idx)

        return selected_rows

    def task_descs(self):
        descs = []
        for task in self.model.tasks():
            descs.append(task.description)

        return descs

    def add(self, task_object):
        self.insert_task(len(self.model), task_object)


class NewCustomListWidget(QListWidget):
    drag_event = pyqtSignal(int)
    drop_event = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_drag_index = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMaximumWidth(300)

    def startDrag(self, *args, **kwargs):
        print('<DRAG STARTED> ', self.parent().name)
        self.current_drag_index = self.currentIndex().row()
        self.drag_event.emit(self.current_drag_index)
        super().startDrag(*args, **kwargs)

    def dropEvent(self, event):
        new_item_pos = self.indexAt(event.pos()).row()
        print('1.)', new_item_pos)

        drop_indicator = self.dropIndicatorPosition()
        print('2.)', drop_indicator)
        if event.source() == self:
            if drop_indicator == 3:
                new_item_pos = self.count() - 1
            print('3.)', new_item_pos)
        else:
            if drop_indicator == 2:
                new_item_pos += 1
            elif drop_indicator == 3:
                new_item_pos = self.count()
            print('4.)', new_item_pos)

        self.drop_event.emit(new_item_pos, drop_indicator)

    def mouseDoubleClickEvent(self, event):
        x = 42


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


class TodoWidget(QWidget):

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
        task = self.create_task(task_text)
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
        delete_icon = resource.get_icon('delete_icon')
        for task in self.storage.tasks(self.name):
            QApplication.processEvents()
            widget = self.create_task(task['name'], delete_icon)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())

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

        if task['name'] in self.storage.task_names(self.name):
            print('This task already exists')
            return

        self.storage.add_task(self.name, task)

        widget = self.create_task(task['name'])
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
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

    def review_task(self, name):
        task = self.storage.get_task(self.name, name)
        review_task_dialog = ReviewTaskDialog(task)
        review_task_dialog.accepted.connect(self.update_task)
        review_task_dialog.exec_()

    def update_task(self, old_task, new_task):
        task_widget = self.create_task(new_task['name'])

        old_index = self.storage.find_task(self.name, old_task['name'])
        item = self.lw.item(old_index)
        self.lw.setItemWidget(item, task_widget)

        self.storage.update_task_at(self.name, old_index, new_task)

    def create_task(self, data, icon=None):
        widget = TaskWidget(data, icon)
        widget.on_remove.connect(self.remove_task)
        widget.on_review.connect(self.review_task)
        return widget



class TodoActions(QWidget):

    def __init__(self, todo_widget=None, parent=None):
        super().__init__(parent)

        self.todo_widget = todo_widget
        self.selection_flag = False

        self.todoname_lbl = QLabel(todo_widget.name)

        self.select = QToolButton(self)
        icon = resource.get_icon('select_icon')
        self.select.setIcon(icon)
        self.select.setMaximumSize(20, 20)
        self.select.setAutoRaise(True)
        self.select.clicked.connect(self.selection_triggered)

        self.delete = QToolButton(self)
        icon = resource.get_icon('delete_icon')
        self.delete.setIcon(icon)
        self.delete.setMaximumSize(20, 20)
        self.delete.setAutoRaise(True)
        self.delete.clicked.connect(self.delete_triggered)

        self.add = QToolButton(self)
        icon = resource.get_icon('add_icon')
        self.add.setIcon(icon)
        self.add.setMaximumSize(20, 20)
        self.add.setAutoRaise(True)
        self.add.clicked.connect(self.run_add_task_dialog)

        layout = QHBoxLayout(self)
        # Set spacing and margins instead of widget size
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        ###
        layout.addWidget(self.todoname_lbl)
        layout.addStretch(1)
        layout.addWidget(self.select)
        layout.addWidget(self.delete)
        layout.addWidget(self.add)
        layout.addStretch(1)
        self.setLayout(layout)

    def selection_triggered(self):
        if not self.selection_flag:
            self.todo_widget.turn_on_selection()
            self.selection_flag = True
            self.add.setDisabled(True)
        else:
            self.todo_widget.turn_off_selection()
            self.selection_flag = False
            self.add.setEnabled(True)

    def delete_triggered(self):
        if self.selection_flag:
            self.todo_widget.remove_selected_items()

    def run_add_task_dialog(self):
        dialog = AddTaskDialog(self.todo_widget.task_descs())
        dialog.accepted.connect(self.todo_widget.add)
        dialog.exec_()



class TodoManager(QWidget):

    def __init__(self, sidebar, storage, parent=None):
        super().__init__(parent)

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.display_or_remove)
        self.sidebar.itemremoved.connect(self.remove_if_exists)
        self.storage = storage
        self.cq = None  # current todo
        self.todos = {}

        self.todolayout = QHBoxLayout()
        self.setLayout(self.todolayout)

    def display_or_remove(self, todo_name):
        if todo_name in self.todos:
            self.remove_todo(todo_name)
        else:
            self.display_todo(todo_name)

    def remove_if_exists(self, todo_name):
        if todo_name in self.todos:
            self.remove_todo(todo_name)

    def display_todo(self, name):
        container = QWidget(self)
        todo_widget = TodoWidget(name, self.storage, container)
        todo_actions = TodoActions(todo_widget, container)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(todo_actions)
        layout.addWidget(todo_widget)
        container.setLayout(layout)
        container.setFixedWidth(300)

        self.todos[name] = container
        self.todolayout.addWidget(container)
        todo_widget.load()

    def remove_todo(self, name):
        container = self.todos[name]
        self.todolayout.removeWidget(container)
        container.deleteLater()
        self.todos.pop(name)



class TodoSidebar(QWidget):

    itemclicked = pyqtSignal(str)
    itemremoved = pyqtSignal(str)

    def __init__(self, storage, parent=None):
        super().__init__(parent)

        self.storage = storage
        self.sidebar = Sidebar(parent=self)
        self.sidebar.itemclicked.connect(self.handle_item_clicked)

        self.add_todo_btn = QToolButton()
        self.add_todo_btn.setIcon(resource.get_icon('add_icon'))
        self.add_todo_btn.setIconSize(QSize(30, 30))
        self.add_todo_btn.setAutoRaise(True)
        self.add_todo_btn.clicked.connect(self.run_dialog)

        self.remove_mode_flag = False
        self.remove_todo_btn = QToolButton()
        self.remove_todo_btn.setIcon(resource.get_icon('delete_icon'))
        self.remove_todo_btn.setIconSize(QSize(30, 30))
        self.remove_todo_btn.setAutoRaise(True)
        self.remove_todo_btn.clicked.connect(self.toggle_remove_mode)


        mlayout = QHBoxLayout()
        mlayout.addWidget(self.sidebar)
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.add_todo_btn)
        btn_layout.addWidget(self.remove_todo_btn)
        mlayout.addLayout(btn_layout)
        self.setLayout(mlayout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

    def add_widget(self, widget, name):
        self.sidebar.add_widget(widget, name)

    def handle_item_clicked(self, name):
        if self.remove_mode_flag:
            self.sidebar.remove_widget(name)
            self.storage.remove_todo(name)
            self.itemremoved.emit(name)
        else:
            self.itemclicked.emit(name)

    def run_dialog(self):
        add_todo_dialog = AddTodoDialog(self.storage.todos())
        add_todo_dialog.accepted.connect(self.add_todo)
        add_todo_dialog.exec_()

    def add_todo(self, name):
        print('Adding:', name)
        self.storage.add_todo(name)
        widget = SidebarButton(name)
        widget.setFixedSize(80, 20)
        self.sidebar.add_widget(widget, name)

    def toggle_remove_mode(self):
        self.remove_mode_flag = not self.remove_mode_flag
        if self.remove_mode_flag:
            self.add_todo_btn.setDisabled(True)
        else:
            self.add_todo_btn.setEnabled(True)

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


class AddTodoDialog(QDialog):

    accepted = pyqtSignal(str)
    rejected = pyqtSignal(bool)

    def __init__(self, todo_names, parent=None):
        super().__init__(parent)

        self.todo_names = todo_names

        self.qname = QLineEdit(self)
        self.qname.setPlaceholderText('Todo Name')
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
        todo_name = self.qname.text()
        if todo_name in self.todo_names:
            self.qname.setStyleSheet('border: 1px solid red;')
            return

        self.accepted.emit(todo_name)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()
