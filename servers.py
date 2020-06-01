import json
import socket
import urllib
import asyncio
from bin import *

def fire_and_forget(f):
    def wrapped(*args, **kwargs): return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)
    return wrapped

# load servers.json -> get all servers type, addr, port
class Servers:
    def __init__(self):
        self.refresh()

    # refresh query server list
    def refresh(self):
        servers = self.get()

        # get country code from ipinfo.io
        is_edited = False
        for server in servers:
            if 'country' not in server:
                try:
                    with urllib.request.urlopen(f'https://ipinfo.io/{socket.gethostbyname(server["addr"])}/country') as response:
                        country = response.read().decode("utf8")
                        if '{' not in country: # may response error json
                            server['country'] = country.rstrip() # rstrip is used because of \n
                            is_edited = True
                except:
                    pass

        if is_edited:
            with open('configs/servers.json', 'w', encoding='utf8') as file:
                json.dump(servers, file, ensure_ascii=False, indent=4)

        self.servers = servers 

    # get servers data
    def get(self):
        with open('configs/servers.json', 'r') as file:
            data = file.read()

        return json.loads(data)

    # add a server
    def add(self, type, game, addr, port, channel):
        data = {}
        data['type'], data['game'] = type, game
        data['addr'], data['port'] = addr, int(port)
        data['channel'] = int(channel)

        servers = self.get()
        servers.append(data)

        with open('configs/servers.json', 'w', encoding='utf8') as file:
            json.dump(servers, file, ensure_ascii=False, indent=4)

    # delete a server by id
    def delete(self, id):
        servers = self.get()
        if 0 < int(id) <= len(servers):
            del servers[int(id) - 1]

            with open('configs/servers.json', 'w', encoding='utf8') as file:
                json.dump(servers, file, ensure_ascii=False, indent=4)
            
            return True
        return False

    def query(self):
        for server in self.servers:
            try:
                self.query_save_cache(server)
            except:
                pass
        return len(self.servers)

    @fire_and_forget
    def query_save_cache(self, server):
        if server['type'] == 'SourceQuery':
            query = SourceQuery(str(server['addr']), int(server['port']))
            result = query.getInfo()
            query.disconnect()

            server_cache = ServerCache(server['addr'], server['port'])
            if result:
                server_cache.save_data(server['game'], result['GamePort'], result['Hostname'], result['Map'], result['MaxPlayers'], result['Players'], result['Bots'], result['Password'] == 0x01)
            else:
                server_cache.set_status('Offline')

        elif server['type'] == 'UT3Query':
            query = UT3Query(str(server['addr']), int(server['port']))
            result = query.getInfo()
            query.disconnect()

            server_cache = ServerCache(server['addr'], server['port'])
            if result:
                server_cache.save_data(server['game'], result['hostport'], result['hostname'], result['map'], result['maxplayers'], result['numplayers'], 0, False)
            else:
                server_cache.set_status('Offline')

        elif server['type'] == 'GamedigQuery':
            query = GamedigQuery(str(server['game']), str(server['addr']), int(server['port']))
            result = query.getInfo()

            server_cache = ServerCache(server['addr'], server['port'])
            if result:
                server_cache.save_data(server['game'], server['port'], result['Hostname'], result['Map'], result['MaxPlayers'], result['Players'], result['Bots'], result['Password'])
            else:
                server_cache.set_status('Offline')



# Game Server Data
class ServerCache:
    def __init__(self, addr, port):
        self.addr, self.port = addr, port
        self.file_name = addr.replace(':', '.') + '-' + str(port)
        self.file_name = "".join(i for i in self.file_name if i not in "\/:*?<>|")

    def get_status(self):
        try:
            with open(f'cache/{self.file_name}.txt', 'r', encoding='utf8') as file:
                return file.read()
        except:
            return False

    def set_status(self, status):
        with open(f'cache/{self.file_name}.txt', 'w', encoding='utf8') as file:
            file.write(str(status))

    def get_data(self):
        try:
            with open(f'cache/{self.file_name}.json', 'r', encoding='utf8') as file:
                return json.load(file)
        except EnvironmentError:
            return False

    def save_data(self, game, gameport, name, map, maxplayers, players, bots, password):
        data = {}

        # save game name, ip address, query port
        data['game'], data['addr'], data['port'] = game, self.addr, gameport

        # save server name, map name, max players count
        data['name'], data['map'], data['maxplayers'] = name, map, maxplayers

        # save current players count, bots count
        data['players'], data['bots'], data['password'] = players, bots, password

        self.set_status('Online')

        with open(f'cache/{self.file_name}.json', 'w', encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)