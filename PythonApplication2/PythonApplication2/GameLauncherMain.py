from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import sys
from AddGamesWindow import AddGamesWindow
from GameLauncher import GameLauncher
from ButtonManager import ButtonManager  # Ensure this matches the file name exactly
import BackgroundManager  # Import BackgroundManager
from tkinter import Canvas, Scrollbar, Frame

class MainWindow(QMainWindow):
    def __init__(self):
        print("Initializing MainWindow")
        super().__init__()
        self.initUI()
        self.button_manager = ButtonManager(self.central_widget_layout, self.games, self.central_widget, self)  # Initialize ButtonManager
        print("MainWindow initialized")

    def initUI(self):
        print("Initializing UI")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Game Manager')

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget_layout = QVBoxLayout(self.central_widget)

        self.add_games_button = QPushButton('Add Games', self)
        self.add_games_button.clicked.connect(self.open_add_games_window)
        self.central_widget_layout.addWidget(self.add_games_button)

        self.games = []  # List to store added games

    def create_canvas(self, parent):
        canvas = Canvas(parent)
        return canvas

    def create_scrollbar(self, parent, canvas):
        scrollbar = Scrollbar(parent, orient="vertical", command=canvas.yview)
        return scrollbar

    def create_frame(self, canvas):
        frame = Frame(canvas)
        return frame

    def open_add_games_window(self):
        print("Opening Add Games Window")
        games = self.get_available_games()  # Method to get the list of available games
        self.add_games_window = AddGamesWindow(self, games)
        self.add_games_window.games_added.connect(self.handle_games_added)
        self.add_games_window.exec_()

    def handle_games_added(self, games):
        self.games.extend(games)
        self.games = sorted(self.games, key=lambda game: os.path.basename(game).lower())  # Sort games alphabetically
        self.update_config()

    def get_available_games(self):
        # Dummy implementation, replace with actual logic to get available games
        return [
            "C:\\Games\\GameA.exe",
            "C:\\Games\\GameB.exe",
            "C:\\Games\\GameC.exe"
        ]

    def update_config(self):
        # Method to update the config with the sorted list of games
        with open('config.txt', 'w') as config_file:
            for game in self.games:
                config_file.write(game + '\n')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
