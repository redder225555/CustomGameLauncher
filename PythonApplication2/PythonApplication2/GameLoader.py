import os
import json

EXECUTED_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(EXECUTED_DIR, "games_config.json")

class GameLoader:
    def __init__(self):
        self.games = []

    def load_games(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                try:
                    self.games = json.load(file)
                    if not isinstance(self.games, list):
                        raise ValueError("Invalid format: games should be a list")
                    for game in self.games:
                        if not isinstance(game, dict) or "name" not in game or "path" not in game:
                            raise ValueError("Invalid format: each game should be a dictionary with 'name' and 'path'")
                except (json.JSONDecodeError, ValueError) as e:
                    self.games = []
        else:
            self.games = []
        return self.games

    def save_games(self, games):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(games, file)
