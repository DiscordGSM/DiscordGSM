import json

class Settings:
    @staticmethod
    def get():
        with open('config/settings.json', 'r', encoding='utf8') as file:
            return json.load(file)