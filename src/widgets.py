from PyQt5.QtWidgets import QWidget, QLayout, QPushButton, QScrollArea, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QToolButton
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPalette

from resources.manager import resource

import time


class FlowLayout(QLayout):
    def __init__(self, max_height=None, parent=None, margin=0, spacex=5, spacey=5):
        super().__init__(parent)

        self.max_height = max_height if max_height else 10000

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
        super().setGeometry(rect)

        final_height = self.resize_layout(rect)
        parent = self.parent()
        if final_height != parent.height() and final_height <= self.max_height:
            parent.setFixedHeight(final_height)
        elif final_height == parent.height():
            # TODO: Resize items to fit into max_height
            pass

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
            item_size_hint = item.sizeHint()
            item_width = item_size_hint.width()
            item_height = item_size_hint.height()

            nextx = x + item_width + sx
            # print('x, item.sizeHint(), sx, nextxm, rect: ', x, item.sizeHint(), sx, nextx, rect)
            if nextx - sx > rect.right() and line_height > 0:
                # print('Go to new line...')
                x = rect.x()
                y = y + line_height + sy
                nextx = x + item_width + sx
                # going to new line, set line_height to 0.
                line_height = 0

            item.setGeometry(QRect(QPoint(x, y), item_size_hint))

            x = nextx
            # Check if this item has the biggest height of all the items in current line.
            line_height = max(line_height, item_height)
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


class SidebarButton(QPushButton):

    def __init__(self, name, parent=None):
        # Name should be same as text
        super().__init__(name, parent)

        self.name = name
        self.setObjectName('SidebarButton')
        self.setCheckable(True)


class Sidebar(QScrollArea):

    itemclicked = pyqtSignal(str)

    def __init__(self, model=None, max_height=100, parent=None):
        super().__init__(parent)

        self.setMaximumHeight(max_height)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.sidebar_widget = QWidget(self)
        self.layout = FlowLayout()
        self.sidebar_widget.setLayout(self.layout)
        self.setWidget(self.sidebar_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)

        self.model = model
        self.widgets = []
        self._load()

    def _load(self):
        for todo in self.model.todos():
            self.add_widget(todo)

    def setup_widget(self, widget, name):
        print('Adding new widget...')
        widget.clicked.connect(lambda: self.item_clicked(name))
        self.layout.addWidget(widget)
        self.widgets.append(widget)

    def remove_widget(self, name):
        for idx, widget in enumerate(self.widgets):
            if widget.name == name:
                self.widgets.pop(idx)
                widget.deleteLater()
                return

        assert False, 'Widget with name {} is not present'.format(name)

    def item_clicked(self, name):
        self.itemclicked.emit(name)

    def mousePressEvent(self, event):
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.red)
        self.sidebar_widget.setAutoFillBackground(True)
        self.sidebar_widget.setPalette(palette)

    def mouseDoubleClickEvent(self, event):
        self.sidebar_widget.setPalette(self.parent().palette())

    def add_widget(self, name):
        widget = SidebarButton(name)
        min_width = 80
        preferred_width = widget.sizeHint().width() + 20
        width = max(min_width, preferred_width)
        widget.setMinimumWidth(width)
        widget.setMaximumHeight(20)
        self.setup_widget(widget, name)

    def widget_names(self):
        return self.model.todos()

