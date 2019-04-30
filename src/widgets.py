from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QGroupBox, QDialog, QTextEdit, QLineEdit, QWidget, QLayout, QSizePolicy, \
    QListWidget, QListWidgetItem, QListView, QAbstractItemView
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal

from random import randint


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacex=5, spacey=5):
        super(FlowLayout, self).__init__(parent)

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
        super(FlowLayout, self).setGeometry(rect)
        self.resize_layout(rect)

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
            nextx = x + item.sizeHint().width() + sx
            # print('x, item.sizeHint(), sx, nextxm, rect: ', x, item.sizeHint(), sx, nextx, rect)
            if nextx - sx > rect.right() and line_height > 0:
                # print('Go to new line...')
                x = rect.x()
                y = y + line_height + sy
                nextx = x + item.sizeHint().width() + sx
                # going to new line, set line_height to 0.
                line_height = 0

            item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextx
            # Check if this item has the biggest height of all the items in current line.
            line_height = max(line_height, item.sizeHint().height())
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



class Sidebar(QWidget):
    """
    You pass sidebar widget to managers, so manager widgets can react to itemclicked signal.
    """

    itemclicked = pyqtSignal(str)

    def __init__(self, parent=None, maxheight=200, maxwidth=500):
        super().__init__(parent)
        self.layout = FlowLayout()
        self.setLayout(self.layout)
        # self.mapper = {}

    def add_widget(self, widget, name):
        print('Adding new widget...')
        # self.mapper[name] = widget
        widget.clicked.connect(lambda: self.item_clicked(name))
        self.layout.addWidget(widget)

    def item_clicked(self, name):
        self.itemclicked.emit(name)


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
        self.lw.clicked.connect(lambda: self.add('SOME TASK', {'start_time': 13.30, 'end_time': 15.7}))

        self.setStyleSheet('background: #FFAA22;')

    def update_drag(self, index):
        self.drag_index = index

    def move_items(self, drop_index):
        self.storage.move_task_by_index(self.name, self.drag_index, drop_index)

    def load(self):
        for task in self.storage.tasks(self.name):
            item = QListWidgetItem(task[0], self.lw)

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
        self.lw.clear()
        self.load()


class QueueActions(QWidget):

    task_created = pyqtSignal(list)

    def __init__(self, queue_widget=None, parent=None):
        super().__init__(parent)

        self.queue_widget = queue_widget

        mlayout = QVBoxLayout()

        self.add_task_btn = QPushButton('Add Task')
        self.add_task_btn.clicked.connect(self.run_add_task_dialog)
        self.remove_task_btn = QPushButton('Remove Task')
        self.select_tasks = QPushButton('Select Tasks')

        mlayout.addWidget(self.add_task_btn)
        mlayout.addWidget(self.remove_task_btn)
        mlayout.addWidget(self.select_tasks)
        self.setLayout(mlayout)

    def set_queue_widget(self, queue_widget):
        self.queue_widget = queue_widget

    def run_add_task_dialog(self):
        dialog = AddTaskDialog(self.queue_widget.task_names())
        dialog.accepted.connect(self.emit_task)
        dialog.exec_()

    def emit_task(self, task):
        self.task_created.emit(task)


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
        mlayout.addWidget(self.qa)

        self.setLayout(mlayout)

        self.sidebar = sidebar
        self.sidebar.itemclicked.connect(self.display_queue)
        self.storage = storage
        self.cq = None  # current queue

    def display_queue(self, name):
        if not self.cq:
            self.cq = QueueWidget(name, self.storage)
        elif self.cq.name != name:
            self.layout.removeWidget(self.cq)
            self.cq = QueueWidget(name, self.storage)
        else:
            return

        self.qa.set_queue_widget(self.cq)
        self.qa.task_created.connect(self.cq.add)
        self.layout.addWidget(self.cq)
        self.cq.load()



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = Sidebar()
    w.show()
    app.exec_()
