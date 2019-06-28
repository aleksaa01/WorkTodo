from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QSizePolicy, QApplication, \
    QScrollArea
from PyQt5.QtCore import pyqtSignal, QSize, Qt

from widgets import Sidebar, TimeEdit
from tasks.widgets import AddTaskDialog, TaskWidget
from tasks.models import TasksModel
from tasks.actions import Action
from resources.manager import resource
from cards.rules import Rules

import time
import datetime


class CardWidgetManager(QScrollArea):

    def __init__(self, sidebar, parent=None):
        super().__init__(parent)

        self.sidebar = sidebar
        self.sidebar.item_clicked.connect(self.display_or_remove)
        self.sidebar.item_removed.connect(self.remove_if_exists)

        self.mwidget = QWidget()
        self.mlayout = QHBoxLayout()
        self.mwidget.setLayout(self.mlayout)
        self.setWidget(self.mwidget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)
        
        self._card_mapper = {}

        self.drag_index = None
        self.drag_source = None
        self.drop_index = None
        self.drop_source = None

    def display_or_remove(self, card_name):
        if card_name in self._card_mapper:
            self.remove_card(card_name)
        else:
            self.display_card(card_name)

    def remove_if_exists(self, card_name):
        if card_name in self._card_mapper:
            self.remove_card(card_name)

    def remove_card(self, card_name):
        card_widget = self._card_mapper[card_name]
        self.mlayout.removeWidget(card_widget)
        # FIXME: Deleting a parent seems like a weird thing to do,
        #   but having container complicates things, because you now
        #   you have to get a card_widget from a container somehow or
        #   you have to store containers too. Just make a new widget that
        #   will hold both card_widget and card_actions.
        card_widget.parent().deleteLater()
        self._card_mapper.pop(card_name)

    def display_card(self, card_name):
        container = QWidget(self)
        card_widget = CardWidget(card_name, container)
        card_widget.drag_event.connect(self.update_drag)
        card_widget.drop_event.connect(self.update_drop)
        card_actions = CardActions(card_widget, container)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(card_actions)
        layout.addWidget(card_widget)
        container.setLayout(layout)
        container.setFixedWidth(300)

        self._card_mapper[card_name] = card_widget
        self.mlayout.addWidget(container)
        card_widget.load()

    def update_drag(self, card_name, index):
        self.drag_source = self._card_mapper[card_name]
        self.drag_index = index

    def update_drop(self, card_name, drop_index, indicator):
        drop_source = self._card_mapper[card_name]
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


class CardWidget(QWidget):
    drag_event = pyqtSignal(str, int)
    drop_event = pyqtSignal(str, int, int)

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name

        self.lw = CustomListWidget(self)
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

        self.rules = Rules(self.name)
        self.rules_warning_icon = resource.get_icon('warning_icon')
        self.rules_danger_icon = resource.get_icon('danger_icon')

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
        if self.rules.isset():
            warning_time = self.rules["warning"]
            danger_time = self.rules["danger"]
        current_time = datetime.datetime.now().timestamp()
        for task_object in self.model.tasks():
            icon = None
            if self.rules.isset():
                if task_object.date + danger_time <= current_time:
                    icon = self.rules_danger_icon
                elif task_object.date + warning_time <= current_time:
                    icon = self.rules_warning_icon

            task_widget = TaskWidget(task_object.description, self.actions, icon)
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


class CustomListWidget(QListWidget):
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

        drop_indicator = self.dropIndicatorPosition()
        if event.source() == self:
            if drop_indicator == 3:
                new_item_pos = self.count() - 1
        else:
            if drop_indicator == 2:
                new_item_pos += 1
            elif drop_indicator == 3:
                new_item_pos = self.count()

        self.drop_event.emit(new_item_pos, drop_indicator)


class CardActions(QWidget):

    def __init__(self, card_widget=None, parent=None):
        super().__init__(parent)

        self.card_widget = card_widget
        self.selection_flag = False

        self.cardname_lbl = QLabel(card_widget.name)

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

        self.rules = QToolButton(self)
        icon = resource.get_icon('rules_icon')
        self.rules.setIcon(icon)
        self.rules.setMaximumSize(20, 20)
        self.rules.setAutoRaise(True)
        self.rules.clicked.connect(self.run_rules_dialog)

        layout = QHBoxLayout(self)
        # Set spacing and margins instead of widget size
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        ###
        layout.addWidget(self.cardname_lbl)
        layout.addStretch(1)
        layout.addWidget(self.select)
        layout.addWidget(self.delete)
        layout.addWidget(self.add)
        layout.addWidget(self.rules)
        layout.addStretch(1)
        self.setLayout(layout)

    def selection_triggered(self):
        if not self.selection_flag:
            self.card_widget.turn_on_selection()
            self.selection_flag = True
            self.add.setDisabled(True)
        else:
            self.card_widget.turn_off_selection()
            self.selection_flag = False
            self.add.setEnabled(True)

    def delete_triggered(self):
        if self.selection_flag:
            self.card_widget.remove_selected_items()

    def run_add_task_dialog(self):
        dialog = AddTaskDialog(self.card_widget.task_descs())
        dialog.accepted.connect(self.card_widget.add)
        dialog.exec_()

    def change_rules(self, rules={}):
        self.card_widget.rules = rules

    def run_rules_dialog(self):
        dialog = RulesDialog(self.card_widget.rules())
        dialog.accepted.connect(self.change_rules)
        dialog.exec_()


class CardSidebar(QWidget):

    item_clicked = pyqtSignal(str)
    item_removed = pyqtSignal(str)

    def __init__(self, model, max_size=100, parent=None):
        super().__init__(parent)

        self.mlayout = QHBoxLayout()

        self.sidebar = Sidebar(model, max_size, self)
        self.sidebar.itemclicked.connect(self.handle_item_clicked)

        self.add_btn = QToolButton(self)
        icon = resource.get_icon('add_icon')
        self.add_btn.setIcon(icon)
        self.add_btn.setIconSize(QSize(30, 30))
        self.add_btn.setMaximumSize(30, 30)
        self.add_btn.setAutoRaise(True)
        self.add_btn.clicked.connect(self.run_add_dialog)

        self.remove_btn = QToolButton(self)
        icon = resource.get_icon('delete_icon')
        self.remove_btn.setIcon(icon)
        self.remove_btn.setIconSize(QSize(30, 30))
        self.remove_btn.setMaximumSize(30, 30)
        self.remove_btn.setAutoRaise(True)
        self.remove_btn.clicked.connect(self.toggle_remove_mode)

        layout = QVBoxLayout()
        layout.addWidget(self.add_btn)
        layout.addWidget(self.remove_btn)

        self.mlayout.addWidget(self.sidebar)
        self.mlayout.addLayout(layout)
        self.setLayout(self.mlayout)

        self.in_remove_mode = False

    def handle_item_clicked(self, str):
        if self.in_remove_mode:
            self.sidebar.remove_widget(str)
            self.item_removed.emit(str)
        else:
            self.item_clicked.emit(str)

    def run_add_dialog(self):
        dialog = AddCardDialog(self.sidebar.widget_names())
        dialog.accepted.connect(self.add_widget)
        dialog.exec_()

    def add_widget(self, widget_name):
        self.sidebar.add_widget(widget_name)

    def toggle_remove_mode(self):
        self.in_remove_mode = not self.in_remove_mode
        if self.in_remove_mode:
            self.add_btn.setDisabled(True)
        else:
            self.add_btn.setEnabled(True)


class AddCardDialog(QDialog):

    accepted = pyqtSignal(str)
    rejected = pyqtSignal(bool)

    def __init__(self, card_names, parent=None):
        super().__init__(parent)

        self.card_names = card_names

        self.qname = QLineEdit(self)
        self.qname.setPlaceholderText('Card Name')
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
        card_name = self.qname.text()
        if card_name in self.card_names:
            self.qname.setStyleSheet('border: 1px solid red;')
            return

        self.accepted.emit(card_name)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class RulesDialog(QDialog):

    def __init__(self, rules, parent=None):
        super().__init__(parent)

        self.rules = rules

        self.warning_lbl = QLabel('Mark as warning after how many seconds')
        self.danger_lbl = QLabel('Mark as danger after how many seconds')
        self.warning_time = TimeEdit(self.rules["warning"], self)
        self.danger_time = TimeEdit(self.rules["danger"], self)

        mlayout = QVBoxLayout()
        lay1 = QVBoxLayout()
        lay1.addWidget(self.warning_lbl)
        lay1.addWidget(self.warning_time)
        lay2 = QVBoxLayout()
        lay2.addWidget(self.danger_lbl)
        lay2.addWidget(self.danger_time)

        mlayout.addLayout(lay1)
        mlayout.addLayout(lay2)
        self.setLayout(mlayout)

