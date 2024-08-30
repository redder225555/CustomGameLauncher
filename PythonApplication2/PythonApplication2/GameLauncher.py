import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QAction, QFileDialog, QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from GameLoader import GameLoader
from ButtonManager import ButtonManager

class GameLauncher(QMainWindow):
    def __init__(self):
        super(GameLauncher, self).__init__()
        self.setWindowTitle("Game Library")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.game_loader = GameLoader()
        self.games = self.game_loader.load_games()

        self.background_manager = BackgroundManager(self.central_widget, "C:/Users/rich/Documents/4kimg.jpg")

        # Pass the main window (self) to the ButtonManager
        self.button_manager = ButtonManager(self.layout, self.games, self.central_widget, self)
        self.button_manager.create_buttons()

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        add_game_action = QAction('Add Game', self)
        add_game_action.triggered.connect(self.add_game)
        file_menu.addAction(add_game_action)

    def add_game(self):
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            exe_files = self.search_exe_files(directory)
            if exe_files:
                self.show_exe_selection_dialog(exe_files)

    def search_exe_files(self, directory):
        exe_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".exe"):
                    exe_files.append(os.path.join(root, file))
        return exe_files

    def show_exe_selection_dialog(self, exe_files):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Games to Add")
        dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)
        for exe_file in exe_files:
            item = QListWidgetItem(os.path.basename(exe_file))
            item.setData(Qt.UserRole, exe_file)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.add_selected_games(list_widget))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def add_selected_games(self, list_widget):
        new_games = []
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.isSelected():
                file_path = item.data(Qt.UserRole)
                game_name = os.path.splitext(os.path.basename(file_path))[0]
                new_games.append({"name": game_name, "path": file_path})

        # Remove duplicates
        unique_games = {game["path"]: game for game in self.games + new_games}.values()
        self.games = sorted(unique_games, key=lambda game: game["name"])

        self.game_loader.save_games(self.games)
        self.button_manager.create_buttons()

    def resizeEvent(self, event):
        try:
            self.background_manager.update_background()
        except Exception as e:
            print(f"Error during resize event: {e}")
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = GameLauncher()
    launcher.show()
    sys.exit(app.exec_())
