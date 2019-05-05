from PyQt5.QtWidgets import QWidget, QLayout, QSizePolicy
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPalette


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



class Sidebar(QWidget):
    """
    You pass sidebar widget to managers, so manager widgets can react to itemclicked signal.
    """

    itemclicked = pyqtSignal(str)

    def __init__(self, max_height=100, parent=None):
        super().__init__(parent)

        self.layout = FlowLayout(max_height)
        self.setLayout(self.layout)

        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.red)
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def add_widget(self, widget, name):
        print('Adding new widget...')
        widget.clicked.connect(lambda: self.item_clicked(name))
        self.layout.addWidget(widget)

    def item_clicked(self, name):
        self.itemclicked.emit(name)
