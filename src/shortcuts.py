from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt



shortcuts = {
    'save': QKeySequence(Qt.CTRL + Qt.Key_S),
    'quit': QKeySequence(Qt.CTRL + Qt.Key_Q),
}

active_shortcuts = []


def set_shortcut(action, callback, parent=None):
    key_sequence = shortcuts[action]
    shortcut = QShortcut(key_sequence, parent)
    shortcut.activated.connect(callback)
    active_shortcuts.append(shortcut)