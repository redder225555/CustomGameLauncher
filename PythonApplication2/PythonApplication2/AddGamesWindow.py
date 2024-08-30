from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QWidget, QCheckBox, QLabel, QMenu, QAction, QInputDialog, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PIL import Image
import win32gui
import win32ui
import win32con
import os  # Import the os module

class AddGamesWindow(QDialog):
    games_added = pyqtSignal(list)  # Signal to emit when games are added

    def __init__(self, parent, games):
        super().__init__(parent)
        self.setWindowTitle("Add Games")
        self.setGeometry(100, 100, 600, 400)
        self.games = sorted(games, key=lambda game: os.path.basename(game).lower())  # Sort games alphabetically

        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Selected Games")
        self.cancel_button = QPushButton("Cancel")
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)
        self.populate_list(self.games)

        self.add_button.clicked.connect(self.add_selected_games)
        self.cancel_button.clicked.connect(self.reject)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        # Removed the connection to show_context_menu
        # self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def populate_list(self, games):
        self.list_widget.clear()
        for game in games:
            icon = self.extract_icon(game)
            item_widget = self.create_item_widget(icon, os.path.basename(game), game)
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

    def create_item_widget(self, icon, game_name, game_path):
        widget = QWidget()
        layout = QHBoxLayout()
        checkbox = QCheckBox()
        icon_label = QLabel()
        icon_label.setPixmap(icon)
        name_label = QLabel(game_name)
        layout.addWidget(checkbox)
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addStretch()
        widget.setLayout(layout)
        widget.checkbox = checkbox
        widget.game_path = game_path
        return widget

    def extract_icon(self, path):
        large, small = win32gui.ExtractIconEx(path, 0)
        if not small:
            return QPixmap(32, 32)  # Return a blank pixmap as a default icon
        win32gui.DestroyIcon(small[0])
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), large[0])
        win32gui.DestroyIcon(large[0])
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRA', 0, 1)
        qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def add_selected_games(self):
        selected_games = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item_widget = self.list_widget.itemWidget(item)
            if item_widget.checkbox.isChecked():
                selected_games.append(item_widget.game_path)
        sorted_selected_games = sorted(selected_games, key=lambda game: os.path.basename(game).lower())  # Sort selected games alphabetically
        self.games_added.emit(sorted_selected_games)  # Emit the signal with the sorted selected games
        self.accept()
