from PyQt5.QtWidgets import QWidget, QLayout, QPushButton, QScrollArea, QSizePolicy, \
    QHBoxLayout, QSpinBox, QLabel, QDialog, QVBoxLayout
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal


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

    def __init__(self, id, text, parent=None):
        super().__init__(text, parent)

        self.id = id
        self.setObjectName('SidebarButton')
        self.setCheckable(True)


class Sidebar(QScrollArea):

    itemclicked = pyqtSignal(str)

    def __init__(self, model=None, max_height=100, parent=None):
        super().__init__(parent)

        self.setMaximumHeight(max_height)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.sidebar_widget = QWidget(self)
        self.sidebar_layout = FlowLayout()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.setWidget(self.sidebar_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)

        self.model = model
        self.load()

    def load(self):
        raise NotImplementedError('load method not implemented.')

    def add_widget(self, widget):
        print('Adding new widget...')
        widget.clicked.connect(self.item_clicked)
        self.sidebar_layout.addWidget(widget)

    def remove_widget(self, id):
        # assumes that widgets have id attribute set
        index = 0
        widget = self.sidebar_layout.itemAt(index)
        while widget:
            if widget.id == id:
                self.sidebar_layout.removeWidget(widget)
                widget.deleteLater()
            index += 1
            widget = self.sidebar_layout.itemAt(index)
            self.model.remove_card(id)
            return

        assert False, 'Widget with id {} is not present'.format(id)

    def item_clicked(self, widget_id):
        self.itemclicked.emit(widget_id)

    def create_widget(self, widget_id, widget_text):
        widget = SidebarButton(widget_id, widget_text)
        min_width = 80
        preferred_width = widget.sizeHint().width() + 20
        width = max(min_width, preferred_width)
        widget.setMinimumWidth(width)
        widget.setMaximumHeight(20)
        return widget


class TimeEdit(QWidget):

    def __init__(self, seconds, parent=None):
        super().__init__(parent)
        if seconds is None:
            seconds = 0

        hours, minutes = 0, 0
        if seconds > 0:
            hours = seconds // 3600
            seconds -= (hours * 3600)
        if seconds > 0:
            minutes = seconds // 60
            seconds -= (minutes * 60)

        self._hours = QSpinBox(self)
        self._hours.setValue(hours)
        self._minutes = QSpinBox(self)
        self._minutes.setValue(minutes)
        self._seconds = QSpinBox(self)
        self._seconds.setValue(seconds)

        mlayout = QHBoxLayout()
        mlayout.addWidget(QLabel("Hours:"))
        mlayout.addWidget(self._hours)
        mlayout.addWidget(QLabel("Minutes:"))
        mlayout.addWidget(self._minutes)
        mlayout.addWidget(QLabel("Seconds:"))
        mlayout.addWidget(self._seconds)
        self.setLayout(mlayout)

    def time(self):
        h = int(self._hours.text())
        m = int(self._minutes.text())
        s = int(self._seconds.text())

        return (h, m, s)

    def seconds(self):
        h, m, s = self.time()
        return s + m * 60 + h * 3600


class SaveDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.message = QLabel("You have unsaved changes.")

        self.savebtn = QPushButton("Save")
        self.savebtn.clicked.connect(self.accept)
        self.cancelbtn = QPushButton("Don't save")
        self.cancelbtn.clicked.connect(self.reject)

        btnlayout = QHBoxLayout()
        btnlayout.addWidget(self.savebtn)
        btnlayout.addWidget(self.cancelbtn)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.message)
        mlayout.addLayout(btnlayout)
        self.setLayout(mlayout)