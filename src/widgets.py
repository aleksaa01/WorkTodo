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

    def __init__(self, parent=None, maxheight=200, maxwidth=500):
        super().__init__(parent)
        self.layout = FlowLayout()
        self.setLayout(self.layout)

    def add_widget(self, widget):
        print('Adding new widget...')
        self.layout.addWidget(widget)

    def add_widgets(self, widget_list):
        for w in widget_list:
            self.layout.addWidget(w)


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
        self._data = []

        self.drag_index = 0
        self.lw = CustomListWidget(self)
        self.lw.dragstarted.connect(self.update_drag)
        self.lw.dropped.connect(self.move_items)
        self.lw.setDragDropMode(QAbstractItemView.InternalMove)

    def update_drag(self, index):
        self.drag_index = index

    def move_items(self, drop_index):
        self.storage.move_task_by_index(self.name, self.drag_index, drop_index)

    def load(self):
        if self._data:
            return
        for task in self.storage.tasks(self.name):
            item = QListWidgetItem(task[0], self.lw)
            self._data.append(task)



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = Sidebar()
    w.show()
    app.exec_()
