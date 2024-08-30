from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt, QTimer

class ScrollingTextEdit(QTextEdit):
    def __init__(self, text, parent=None):
        super(ScrollingTextEdit, self).__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: lightgrey; color: black;")
        self.setText(text)
        self.setFixedHeight(30)  # Set a fixed height for single-line appearance
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.offset = 0
        self.text = text
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        
        if len(text) > 16:
            self.timer.start(300)  # Adjust the interval for slower scrolling speed

    def update_position(self):
        self.offset += 1
        if self.offset > len(self.text):
            self.offset = 0
        display_text = self.text[self.offset:] + " " + self.text[:self.offset]
        self.setPlainText(display_text)
