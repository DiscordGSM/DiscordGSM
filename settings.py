import json

class Settings:
    @staticmethod
    def get():
        with open('configs/settings.json', 'r', encoding='utf8') as file:
            return json.load(file)