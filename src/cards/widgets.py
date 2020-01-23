from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QDialog, QLineEdit, QWidget, QListWidget, QListWidgetItem, \
    QAbstractItemView, QToolButton, QSizePolicy, QApplication, \
    QScrollArea, QMessageBox, QFrame, QCheckBox
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QColor, QPalette, QBrush

from widgets import Sidebar, TimeEdit
from tasks.widgets import TaskWidget, AddTaskDialog, EditTaskDialog
from tasks.models import TasksModel
from tasks.actions import Action
from resources.manager import resource
from cards.preferences import Preferences

import time
import datetime


class CardWidgetManager(QScrollArea):

    def __init__(self, card_model, parent=None):
        super().__init__(parent)
        self.model = card_model
        self.model.on_click(self.show_or_remove)
        self.model.on_remove(self.remove_if_exists)

        self.mwidget = QWidget()
        self.mlayout = QHBoxLayout()
        self.mwidget.setLayout(self.mlayout)
        self.setWidget(self.mwidget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)

        self._active_cards = {}

        self.drag_index = None
        self.drag_source = None

    def show_or_remove(self, card_rid):
        if card_rid in self._active_cards:
            self.remove_card(card_rid)
        else:
            self.show_card(card_rid)

    def remove_if_exists(self, card_rid):
        if card_rid in self._active_cards:
            self.remove_card(card_rid)

    def remove_card(self, card_rid):
        card_widget = self._active_cards[card_rid]
        self.mlayout.removeWidget(card_widget)
        # FIXME: Deleting a parent seems like a weird thing to do,
        #   but having container complicates things, because you now
        #   you have to get a card_widget from a container somehow or
        #   you have to store containers too. Just make a new widget that
        #   will hold both card_widget and card_actions.
        card_widget.parent().deleteLater()
        self._active_cards.pop(card_rid)

    def show_card(self, card_rid):
        container = QWidget(self)
        card_name = self.model.get_name(card_rid)
        task_model = self.model.get_task_model(card_rid)
        preference_model = self.model.get_card_preferences(card_rid)
        card_widget = CardWidget(card_rid, card_name, task_model, preference_model, container)
        card_widget.drag_event.connect(self.update_drag)
        card_widget.drop_event.connect(self.update_drop)
        card_actions = CardActions(card_widget, container)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(card_actions)
        layout.addWidget(card_widget)
        container.setLayout(layout)
        container.setFixedWidth(300)

        self._active_cards[card_rid] = card_widget
        self.mlayout.addWidget(container)
        card_widget.load()

    def update_drag(self, card_rid, index):
        self.drag_source = self._active_cards[card_rid]
        self.drag_index = index

    def update_drop(self, card_rid, drop_index, indicator):
        drop_source = self._active_cards[card_rid]
        if self.drag_source == drop_source:
            drop_index = self._fix_drop_offset(drop_index, indicator)
            drop_source.move_task(self.drag_index, drop_index)
            return

        # it's very important to transfer tasks before we call view methods
        # because view methods relly on models to do their job properly
        self.model.transfer_task(self.drag_source.rid, drop_source.rid,
                                 self.drag_index, drop_index)
        self.drag_source.pop_widget(self.drag_index)
        drop_source.insert_widget(drop_index)

    def _fix_drop_offset(self, drop_index, indicator):
        if self.drag_index < drop_index:
            if indicator == 1:
                drop_index -= 1
        elif self.drag_index > drop_index:
            if indicator == 2:
                drop_index += 1
        return drop_index


class CardWidget(QWidget):
    drag_event = pyqtSignal(int, int)
    drop_event = pyqtSignal(int, int, int)

    def __init__(self, card_rid, card_name, task_model, preference_model, parent=None):
        super().__init__(parent)
        self.rid = card_rid
        self.name = card_name
        self.tmodel = task_model
        self.pmodel = preference_model

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

        self._warning_icon = resource.get_icon('warning_icon')
        self._danger_icon = resource.get_icon('danger_icon')

    def emit_drag_event(self, index):
        print('Drag emmited >>> ', index)
        # FIXME: drag_event should emit rid, not name
        self.drag_event.emit(self.rid, index)

    def emit_drop_event(self, index, indicator):
        print('Drop emmited >>> ', index)
        # FIXME: drop_event should emit rid, not name
        self.drop_event.emit(self.rid, index, indicator)

    def load(self):

        print('Loading data...')
        t1 = time.perf_counter()

        action_remove = Action('Remove', resource.get_icon('delete_icon'))
        action_remove.signal.connect(self.remove_task)
        action_edit = Action('Edit')
        action_edit.signal.connect(self.run_edit_task_dialog)
        self.actions = [action_remove, action_edit]

        show_date = self.pmodel.show_date

        warning_time = self.pmodel.warning_time
        danger_time = self.pmodel.danger_time
        current_time = datetime.datetime.now().timestamp()

        for rid, text, created in self.tmodel.data():
            icon = None
            if danger_time and created + danger_time <= current_time:
                icon = self._danger_icon
            elif warning_time and created + warning_time <= current_time:
                icon = self._warning_icon

            if show_date:
                dt = datetime.datetime.fromtimestamp(created)
                text = "{}\n({}.{}.{} {}:{})".format(text, dt.day, dt.month, dt.year, dt.hour, dt.minute)

            task_widget = TaskWidget(rid, text, self.actions, icon)
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.lw.addItem(item)
            self.lw.setItemWidget(item, task_widget)

            QApplication.processEvents()

        t2 = time.perf_counter()
        print('Time took:', t2 - t1)

    def reload(self):
        self.lw.clear()
        self.load()

    def remove_task(self, pos):
        idx = self.lw.indexAt(self.lw.mapFromGlobal(pos)).row()
        item = self.lw.takeItem(idx)
        del item
        self.tmodel.remove(idx)

    def get_task(self, index):
        return self.tmodel[index]

    def pop_task(self, index):
        item = self.lw.takeItem(index)
        del item
        return self.tmodel.remove(index)

    def pop_widget(self, index):
        item = self.lw.item(index)
        widget = self.lw.itemWidget(item)
        self.lw.takeItem(index)
        return widget

    def insert_widget(self, index):
        rid, text, created = self.tmodel.data(index)

        if self.pmodel.show_date:
            dt = datetime.datetime.fromtimestamp(created)
            text = "{}\n({}.{}.{} {}:{})".format(text, dt.year, dt.month,
                                                 dt.day, dt.hour, dt.minute)

        dtime = self.pmodel.danger_time
        wtime = self.pmodel.warning_time
        icon = None
        now = datetime.datetime.now().timestamp()
        if dtime and dtime + created <= now:
            icon = self._danger_icon
        elif wtime and wtime + created <= now:
            icon = self._warning_icon

        task_widget = TaskWidget(rid, text, self.actions, icon)
        item = QListWidgetItem()
        item.setSizeHint(task_widget.sizeHint())
        self.lw.insertItem(index, item)
        self.lw.setItemWidget(item, task_widget)

    def move_task(self, from_idx, to_idx):
        item = self.lw.item(from_idx)
        widget = self.lw.itemWidget(item)
        text = widget.label.text()
        if widget.icon_btn:
            icon = widget.icon_btn.icon()
        else:
            icon = None
        rid, _, _ = self.tmodel.data(from_idx)
        widget = TaskWidget(rid, text, self.actions, icon)
        self.lw.takeItem(from_idx)

        self.tmodel.move(from_idx, to_idx)

        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.lw.insertItem(to_idx, item)
        self.lw.setItemWidget(item, widget)
        x = 42

    def turn_on_selection(self):
        self.lw.setSelectionMode(QAbstractItemView.NoSelection)
        self.lw.clearSelection()
        for idx in range(len(self.tmodel)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.add_checker()

    def turn_off_selection(self):
        self.lw.setSelectionMode(QAbstractItemView.SingleSelection)
        for idx in range(len(self.tmodel)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            widget.remove_checker()

    def remove_selected_items(self):
        selected_rows = self.get_selected_rows()
        for idx in range(len(selected_rows) - 1, -1, -1):
            self.pop_task(selected_rows[idx])

    def get_selected_rows(self):
        selected_rows = []
        for idx in range(len(self.tmodel)):
            widget = self.lw.itemWidget(self.lw.item(idx))
            if widget.checker.isChecked():
                selected_rows.append(idx)

        return selected_rows

    def add_task(self, text):
        created = datetime.datetime.now().timestamp()
        rid = self.tmodel.add(text, created)

        if self.pmodel.show_date:
            dt = datetime.datetime.fromtimestamp(created)
            text = "{}\n({}.{}.{})".format(text, dt.day, dt.month, dt.year)

        icon = None
        wtime = self.pmodel.warning_time
        dtime = self.pmodel.danger_time
        current_time = datetime.datetime.now().timestamp()
        if dtime and created + dtime <= current_time:
            icon = self._danger_icon
        elif wtime and created + wtime <= current_time:
            icon = self._warning_icon

        task_widget = TaskWidget(rid, text, self.actions, icon)
        item = QListWidgetItem()
        item.setSizeHint(task_widget.sizeHint())
        self.lw.addItem(item)
        self.lw.setItemWidget(item, task_widget)

    def run_edit_task_dialog(self, pos):
        index = self.lw.indexAt(self.lw.mapFromGlobal(pos)).row()
        rid, desc, created = self.tmodel.data(index)
        dialog = EditTaskDialog(desc, created)
        dialog.accepted.connect(lambda desc, created: self.edit_task(index, desc, created))
        dialog.exec_()


    def edit_task(self, index, description, created_at):
        self.tmodel.update(index, description, created_at)
        item = self.lw.item(index)
        widget = self.lw.itemWidget(item)
        dt = datetime.datetime.fromtimestamp(created_at)
        content = "{}\n({}.{}.{} {}:{})".format(description, dt.day, dt.month, dt.year, dt.hour, dt.minute)
        widget.set_text(content)
        item.setSizeHint(widget.sizeHint())


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
            # FIXME: indicator can be 3 if you drop widget in between 2 widgets where the
            #   spacing is big enough.
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
        self.select.setToolTip('Select multiple tasks')
        self.select.clicked.connect(self.selection_triggered)

        self.delete = QToolButton(self)
        icon = resource.get_icon('delete_icon')
        self.delete.setIcon(icon)
        self.delete.setMaximumSize(20, 20)
        self.delete.setAutoRaise(True)
        self.delete.setToolTip('Remove selected tasks')
        self.delete.clicked.connect(self.delete_triggered)

        self.add = QToolButton(self)
        icon = resource.get_icon('add_icon')
        self.add.setIcon(icon)
        self.add.setMaximumSize(20, 20)
        self.add.setAutoRaise(True)
        self.add.setToolTip('Create new task')
        self.add.clicked.connect(self.run_add_task_dialog)

        self.preferences = QToolButton(self)
        icon = resource.get_icon('preferences_icon')
        self.preferences.setIcon(icon)
        self.preferences.setMaximumSize(20, 20)
        self.preferences.setAutoRaise(True)
        self.preferences.setToolTip('Card options')
        self.preferences.clicked.connect(self.run_preferences_dialog)

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
        layout.addWidget(self.preferences)
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
        dialog = AddTaskDialog()
        dialog.accepted.connect(self.card_widget.add_task)
        dialog.exec_()

    def preferences_changed(self):
        self.card_widget.reload()

    def run_preferences_dialog(self):
        dialog = PreferencesDialog(self.card_widget.pmodel)
        dialog.accepted.connect(self.preferences_changed)
        dialog.exec_()


class CardSidebar(Sidebar):

    itemclicked = pyqtSignal(int)
    logout = pyqtSignal()

    def __init__(self, model, max_size=100, parent=None):
        super().__init__(model, max_size, parent)

    def load(self):
        print('IN CardSidebar > load')
        for rid, name in self.model.cards():
            print('rid, name:', rid, name)
            widget = self.create_widget(rid, name)
            print('widget >>>', widget)
            self.add_widget(widget)

    def item_clicked(self, card_rid):
        print('widget id:', card_rid)
        self.itemclicked.emit(card_rid)

    def show(self, card_rid):
        self.model.show_card(card_rid)

    def remove(self, card_rid):
        self.model.remove_card(card_rid)
        self.remove_widget(card_rid)

    def create(self, card_name):
        card_rid = self.model.add_card(card_name)
        wgt = self.create_widget(card_rid, card_name)
        self.add_widget(wgt)


class SidebarContainer(QWidget):
    def __init__(self, sidebar, parent=None):
        super().__init__(parent)

        self.mlayout = QHBoxLayout()

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.handle_item_clicked)

        self.add_btn = QToolButton(self)
        icon = resource.get_icon('add_icon')
        self.add_btn.setIcon(icon)
        self.add_btn.setIconSize(QSize(22, 22))
        self.add_btn.setMinimumSize(22, 22)
        self.add_btn.setAutoRaise(True)
        self.add_btn.setToolTip('Add card')
        self.add_btn.clicked.connect(self.run_add_dialog)

        self.remove_btn = QToolButton(self)
        icon = resource.get_icon('delete_icon')
        self.remove_btn.setIcon(icon)
        self.remove_btn.setIconSize(QSize(22, 22))
        self.remove_btn.setMaximumSize(22, 22)
        self.remove_btn.setAutoRaise(True)
        self.remove_btn.setToolTip('Remove card')
        self.remove_btn.clicked.connect(self.toggle_remove_mode)

        self.logout_btn = QToolButton(self)
        icon = resource.get_icon('logout_icon')
        self.logout_btn.setIcon(icon)
        self.logout_btn.setIconSize(QSize(22, 22))
        self.logout_btn.setMaximumSize(22, 22)
        self.logout_btn.setAutoRaise(True)
        self.logout_btn.setToolTip('Logout')
        self.logout_btn.clicked.connect(lambda: self.sidebar.logout.emit())

        sidebar_actions_layout = QVBoxLayout()
        sidebar_actions_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_actions_layout.setSpacing(0)
        sidebar_actions_layout.addWidget(self.add_btn, 0, Qt.AlignTop)
        sidebar_actions_layout.addWidget(self.remove_btn, 0, Qt.AlignTop)

        logout_layout = QVBoxLayout()
        logout_layout.addWidget(self.logout_btn, 0, Qt.AlignTop)
        logout_layout.setContentsMargins(0, 0, 0, 0)

        sidebar_layout = QHBoxLayout()
        sidebar_layout.setContentsMargins(5, 8, 5, 0)
        sidebar_layout.addWidget(self.sidebar)

        self.mlayout.setContentsMargins(0, 0, 0, 0)
        self.mlayout.addLayout(sidebar_actions_layout)
        self.mlayout.addLayout(sidebar_layout)
        self.mlayout.addLayout(logout_layout)
        self.setLayout(self.mlayout)

        self.in_remove_mode = False

    def handle_item_clicked(self, param):
        if self.in_remove_mode:
            self.sidebar.remove(param)
        else:
            self.sidebar.show(param)

    def run_add_dialog(self):
        dialog = AddCardDialog()
        dialog.accepted.connect(self.add_widget)
        dialog.exec_()

    def add_widget(self, widget_name):
        self.sidebar.create(widget_name)

    def toggle_remove_mode(self):
        self.in_remove_mode = not self.in_remove_mode
        if self.in_remove_mode:
            self.add_btn.setDisabled(True)
        else:
            self.add_btn.setEnabled(True)


class AddCardDialog(QDialog):

    accepted = pyqtSignal(str)
    rejected = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cname = QLineEdit(self)
        self.cname.setPlaceholderText('Card Name')
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.cname)
        mlayout.addLayout(btn_layout)
        self.setLayout(mlayout)

    def accept(self):
        card_name = self.cname.text()
        self.accepted.emit(card_name)
        super().accept()

    def reject(self):
        self.rejected.emit(True)
        super().reject()


class PreferencesDialog(QDialog):

    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, preferences_model, parent=None):
        super().__init__(parent)

        self.pmodel = preferences_model

        warning = self.pmodel.warning_time
        danger = self.pmodel.danger_time
        self.warning_lbl = QLabel('Mark as warning after')
        self.danger_lbl = QLabel('Mark as danger after')
        self.warning_time = TimeEdit(warning, self)
        self.danger_time = TimeEdit(danger, self)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        lay1 = QVBoxLayout()
        lay1.addWidget(self.warning_lbl)
        lay1.addWidget(self.warning_time)
        lay2 = QVBoxLayout()
        lay2.addWidget(self.danger_lbl)
        lay2.addWidget(self.danger_time)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameStyle(QFrame.Sunken)

        show_date_lbl = QLabel("Show date of task creation.")
        self.show_date_checkbox = QCheckBox()
        if self.pmodel.show_date:
            self.show_date_checkbox.setChecked(True)
        else:
            self.show_date_checkbox.setChecked(False)
        lay3 = QHBoxLayout()
        lay3.addWidget(show_date_lbl)
        lay3.addWidget(self.show_date_checkbox)

        lay4 = QHBoxLayout()
        lay4.addWidget(self.ok_btn)
        lay4.addWidget(self.cancel_btn)
        lay4.setContentsMargins(10, 20, 10, 10)

        mlayout = QVBoxLayout()
        mlayout.addLayout(lay1)
        mlayout.addLayout(lay2)
        mlayout.addWidget(line)
        mlayout.addLayout(lay3)
        mlayout.addLayout(lay4)
        self.setLayout(mlayout)

    def accept(self):
        wtime = self.warning_time.seconds()
        dtime = self.danger_time.seconds()
        self.pmodel.warning_time = wtime
        self.pmodel.danger_time = dtime
        self.pmodel.show_date = self.show_date_checkbox.isChecked()
        self.accepted.emit()
        super().accept()

    def reject(self):
        self.rejected.emit()
        super().reject()
