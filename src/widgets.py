from PyQt5.QtWidgets import QWidget, QLayout
from PyQt5.QtCore import QRect, QSize, Qt, QPoint, pyqtSignal


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = FlowLayout()
        self.setLayout(self.layout)

    def add_widget(self, widget, name):
        print('Adding new widget...')
        widget.clicked.connect(lambda: self.item_clicked(name))
        self.layout.addWidget(widget)

    def item_clicked(self, name):
        self.itemclicked.emit(name)
