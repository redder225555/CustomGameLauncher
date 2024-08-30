import os
import json
from functools import partial
from PyQt5.QtWidgets import QAction, QInputDialog, QLineEdit, QMenu, QPushButton, QScrollArea, QVBoxLayout, QWidget, QFileDialog, QGridLayout
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QImage, QPalette, QBrush
from PyQt5.QtCore import QSize, Qt
from PIL import Image
import win32gui
import win32ui
from GameLoader import GameLoader
from AddGamesWindow import AddGamesWindow
from ScrollingTextEdit import ScrollingTextEdit

class ButtonManager:
    CONFIG_FILE = "config.json"

    def __init__(self, parent_layout, games, parent_widget, main_window):
        self.parent_layout = parent_layout
        self.games = games
        self.parent_widget = parent_widget
        self.main_window = main_window
        self.button_size = QSize(150, 150)  # Fixed button size
        self.initialized = False  # Flag to check if buttons are already created

        # Connect to the resize event of the parent widget
        self.original_resize_event = self.parent_widget.resizeEvent
        self.parent_widget.resizeEvent = self.on_resize

        # Add the reload games action to the menu
        self.add_reload_action_to_menu()

        # Add the add games action to the menu
        self.add_add_games_action_to_menu()

        # Add the background image selector action to the menu
        self.add_background_image_selector_to_menu()

        # Load the sort order and background image from the configuration file
        self.sort_order, self.background_image_path = self.load_config()

        # Load games and create buttons initially
        self.reload_games()

        # Set the background image if it exists, otherwise set a default color
        if self.background_image_path:
            self.set_background_image(self.background_image_path)
        else:
            self.set_default_background_color()

    def add_reload_action_to_menu(self):
        reload_action = QAction("Reload Games", self.main_window)
        reload_action.setShortcut(QKeySequence("F5"))
        reload_action.triggered.connect(self.reload_games)
        self.main_window.menuBar().addAction(reload_action)

    def add_add_games_action_to_menu(self):
        add_games_action = QAction("Add Games", self.main_window)
        add_games_action.setShortcut(QKeySequence("Ctrl+N"))
        add_games_action.triggered.connect(self.open_add_games_window)
        self.main_window.menuBar().addAction(add_games_action)

    def add_background_image_selector_to_menu(self):
        background_image_action = QAction("Background Image Selector", self.main_window)
        background_image_action.setShortcut(QKeySequence("Ctrl+B"))
        background_image_action.triggered.connect(self.select_background_image)
        self.main_window.menuBar().addAction(background_image_action)

    def open_add_games_window(self):
        file_dialog = QFileDialog(self.main_window)
        file_dialog.setFileMode(QFileDialog.Directory)
        if file_dialog.exec_():
            folder_path = file_dialog.selectedFiles()[0]
            games = self.scan_for_games(folder_path)
            add_games_window = AddGamesWindow(self.main_window, games)
            add_games_window.games_added.connect(self.add_games)  # Connect the signal
            add_games_window.exec_()

    def scan_for_games(self, folder_path):
        games = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".exe"):
                    games.append(os.path.join(root, file))
        return games

    def add_games(self, new_games):
        for game in new_games:
            self.games.append({"name": os.path.basename(game), "path": game})
        self.create_buttons()
        GameLoader().save_games(self.games)  # Save the updated games list

    def create_buttons(self):

        # Temporarily disconnect the resize event
        self.parent_widget.resizeEvent = None

        # Clear the existing layout
        while self.parent_layout.count():
            child = self.parent_layout.takeAt(0)
            if child.widget():
                print(f"Deleting widget: {child.widget()}")
                child.widget().deleteLater()

        # Create a scroll area for the grid layout
        self.scroll_area = QScrollArea()  # Store reference to QScrollArea
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent;")
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setContentsMargins(0, 0, 10, 0)  # Add right margin to keep distance from scrollbar
        self.grid_layout.setVerticalSpacing(10)  # Set vertical spacing between rows to 10 pixels
        scroll_content.setLayout(self.grid_layout)
        self.scroll_area.setWidget(scroll_content)
        self.parent_layout.addWidget(self.scroll_area)

        self.populate_grid()
        self.initialized = True  # Set the flag to True after initial population

        # Reconnect the resize event
        self.parent_widget.resizeEvent = self.on_resize

    def populate_grid(self):
        # Clear the existing grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        created_game_names = set()
        row, col = 0, 0

        # Calculate the number of columns based on the current width of the scroll area
        scroll_area_width = self.scroll_area.viewport().width()
        max_columns = min(20, max(1, scroll_area_width // self.button_size.width()))


        for game in self.games:
            if not isinstance(game, dict):
                continue
            if game['name'] in created_game_names:
                continue
            created_game_names.add(game['name'])

            icon = self.extract_icon(game["path"])
            resized_icon = self.resize_icon(icon, self.button_size.width(), self.button_size.height())  # Resize icon to button size

            # Create the button with the icon
            button = QPushButton()
            button.setIcon(QIcon(resized_icon))
            button.setIconSize(self.button_size)  # Set icon size to button size
            button.setFixedSize(self.button_size)  # Set button size to match icon size
            button.setStyleSheet("background-color: white; padding: 0px; margin: 0px;")  # Remove padding and margin
            button.clicked.connect(partial(self.launch_game, game["path"]))
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(partial(self.show_context_menu, game, button))

            # Create a scrolling text edit for the game name
            text_edit = ScrollingTextEdit(game["name"])
            text_edit.setFixedWidth(self.button_size.width())  # Adjust text edit width to match the icon width

            # Create a container widget to hold the button and text edit
            container = QWidget()
            container_layout = QVBoxLayout()
            container_layout.addWidget(button)
            container_layout.addWidget(text_edit)
            container_layout.setSpacing(0)  # Set spacing to 0
            container_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            container.setLayout(container_layout)

            # Add the container to the grid layout
            self.grid_layout.addWidget(container, row, col, Qt.AlignTop)  # Align the container to the top
            col += 1
            if col >= max_columns:
                col = 0
                row += 1

    def on_resize(self, event):
        if self.initialized:  # Only repopulate grid if already initialized
            self.populate_grid()
        if self.original_resize_event:
            self.original_resize_event(event)

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

    def resize_icon(self, pixmap, width, height):
        return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def launch_game(self, path):
        os.startfile(path)

    def show_context_menu(self, game, button, position):
        context_menu = QMenu(self.main_window)
        remove_action = context_menu.addAction("Remove Game")
        sort_az_action = context_menu.addAction("Sort A-Z")
        sort_za_action = context_menu.addAction("Sort Z-A")
        rename_action = context_menu.addAction("Rename Game")

        action = context_menu.exec_(button.mapToGlobal(position))
        if action == remove_action:
            self.remove_game(game)
        elif action == sort_az_action:
            self.sort_games(ascending=True)
        elif action == sort_za_action:
            self.sort_games(ascending=False)
        elif action == rename_action:
            self.rename_game(game)

    def remove_game(self, game):
        self.games = [g for g in self.games if g != game]
        self.create_buttons()
        GameLoader().save_games(self.games)  # Save the updated games list

    def sort_games(self, ascending=True):
        self.games = sorted(self.games, key=lambda game: game['name'].lower())
        self.create_buttons()

    def rename_game(self, game):
        new_name, ok = QInputDialog.getText(self.main_window, "Rename Game", "Enter new name:", QLineEdit.Normal, game['name'])
        if ok and new_name:
            game['name'] = new_name
            self.create_buttons()
            GameLoader().save_games(self.games)  # Save the updated games list

    def select_background_image(self):
        file_dialog = QFileDialog(self.main_window)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.jpeg *.bmp)")
        if file_dialog.exec_():
            self.background_image_path = file_dialog.selectedFiles()[0]
            self.set_background_image(self.background_image_path)
            self.save_config()

    def set_background_image(self, image_path):
        self.main_window.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({image_path});
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
            }}
        """)

    def set_default_background_color(self):
        self.main_window.setStyleSheet("QMainWindow { background-color: #f0f0f0; }")

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as file:
                config = json.load(file)
                return config.get('sort_order', []), config.get('background_image_path', '')
        return [], ''

    def save_config(self):
        config = {
            'sort_order': self.sort_order,
            'background_image_path': self.background_image_path
        }
        with open(self.CONFIG_FILE, 'w') as file:
            json.dump(config, file)

    def reload_games(self):
        self.games = GameLoader().load_games()
        self.create_buttons()
