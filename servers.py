import json
from enum import Enum
from bin import *

# 1. Load servers.json -> get all servers type, addr, port
# 2. Query the server by type, addr, port
# 3. Save the servers query data to cache/
class Servers:
    def __init__(self):
        self.load()

    def load(self):
        # read servers.json
        with open('config/servers.json', 'r') as file:
            data = file.read()

        # get servers
        self.servers = json.loads(data)

        return self.servers

    def query(self):
        for server in self.servers:
            if server['type'] == 'SourceQuery':
                query = SourceQuery(str(server['addr']), int(server['port']))
                result = query.getInfo()

                server_cache = ServerCache(server['addr'], server['port'])

                if result:
                    server_cache.set_status('Online')
                    server_cache.save_data(server['game'], result['GamePort'], result['Hostname'], result['Map'], result['MaxPlayers'], result['Players']-result['Bots'], result['Bots'])
                else:
                    server_cache.set_status('Offline')

# Game Server Data
class ServerCache:
    def __init__(self, addr, port):
        self.addr, self.port = addr, port
        self.file_name = addr.replace(':', '.') + '-' + str(port)
        self.file_name = "".join(i for i in self.file_name if i not in "\/:*?<>|")

    def get_status(self):
        with open(f'cache/{self.file_name}-status.txt', 'r', encoding='utf8') as file:
            return file.read()

    def set_status(self, status):
        with open(f'cache/{self.file_name}-status.txt', 'w', encoding='utf8') as file:
            file.write(str(status))

    def get_data(self):
        try:
            with open(f'cache/{self.file_name}.json', 'r', encoding='utf8') as file:
                return json.load(file)
        except EnvironmentError:
            return False

    def save_data(self, game, gameport, name, map, maxplayers, players, bots):
        data = {}

        # save game name, ip address, query port
        data['game'], data['addr'], data['port'] = game, self.addr, gameport

        # save server name, map name, max players count
        data['name'], data['map'], data['maxplayers'] = name, map, maxplayers

        # save current players count, bots count
        data['players'], data['bots'] = players, bots

        with open(f'cache/{self.file_name}.json', 'w', encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
