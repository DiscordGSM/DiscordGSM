import json
import socket
import urllib
import asyncio
from bin import *

def fire_and_forget(f):
    def wrapped(*args, **kwargs): return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)
    return wrapped

# load servers.json -> get all servers type, address, port
class Servers:
    def __init__(self):
        self.refresh()

    # refresh query server list
    def refresh(self):
        servers = self.get()

        # get country code from ipinfo.io
        is_edited = False
        for server in servers:
            if "country" not in server:
                try:
                    with urllib.request.urlopen(f'https://ipinfo.io/{socket.gethostbyname(server["address"])}/country') as response:
                        country = response.read().decode("utf-8")
                        if "{" not in country: # may response error json
                            server["country"] = country.rstrip() # rstrip is used because of \n
                            is_edited = True
                except:
                    pass
        
        #overwrite servers.json if a country is missing
        if is_edited:
           self.update_server_file(servers)

        self.servers = servers 
        return servers

    def update_server_file(self, servers):
        with open("servers.json", "w", encoding="utf-8") as file:
            json.dump(servers, file, ensure_ascii=False, indent=4)

    # get servers data
    def get(self):
        with open("servers.json", "r", encoding="utf-8") as file:
            data = file.read()

        return json.loads(data)

    def get_distinct_server_count(self):       
        uniqueServers = [f'{server["address"]}:{str(server["port"])}' for server in self.servers]
        return len(list(set(uniqueServers)))

    def query(self):
        for server in self.servers:
            try:
                self.query_save_cache(server)
            except:
                pass
        return len(self.servers)

    @fire_and_forget
    def query_save_cache(self, server):
        if str(server["type"]).lower() == "sourcequery":
            query = SourceQuery(str(server["address"]), int(server["port"]))
            result = query.getInfo()
            query.disconnect()

            server_cache = ServerCache(server["address"], server["port"])
            if result:
                server_cache.save_data(server["game"], result["GamePort"], result["Hostname"], result["Map"], result["MaxPlayers"], result["Players"], result["Bots"], result["Password"] == 0x01)
            else:
                server_cache.set_status("Offline")

        elif str(server["type"]).lower() == "ut3query":
            query = UT3Query(str(server["address"]), int(server["port"]))
            result = query.getInfo()
            query.disconnect()

            server_cache = ServerCache(server["address"], server["port"])
            if result:
                server_cache.save_data(server["game"], result["hostport"], result["hostname"], result["map"], result["maxplayers"], result["numplayers"], 0, False)
            else:
                server_cache.set_status("Offline")

        elif str(server["type"]).lower() == "gamedigquery":
            query = GamedigQuery(str(server["game"]), str(server["address"]), int(server["port"]))
            result = query.getInfo()

            server_cache = ServerCache(server["address"], server["port"])
            if result:
                server_cache.save_data(server["game"], server["port"], result["Hostname"], result["Map"], result["MaxPlayers"], result["Players"], result["Bots"], result["Password"])
            else:
                server_cache.set_status("Offline")

        elif str(server["type"]).lower() == "fake":
            server_cache = ServerCache(server["address"], server["port"])
            server_cache.save_data(server["game"], server["port"], None, None, None, None, None, None)

# Game Server Data
class ServerCache:
    def __init__(self, address, port):
        self.address, self.port = address, port
        self.file_name = address.replace(":", ".") + "-" + str(port)
        self.file_name = "".join(i for i in self.file_name if i not in "\/:*?<>|")

    def get_status(self):
        try:
            with open(f'cache/{self.file_name}.txt', "r", encoding="utf-8") as file:
                return file.read()
        except:
            return False

    def set_status(self, status):
        with open(f'cache/{self.file_name}.txt', "w", encoding="utf-8") as file:
            file.write(str(status))

    def get_data(self):
        try:
            with open(f'cache/{self.file_name}.json', "r", encoding="utf-8") as file:
                return json.load(file)
        except EnvironmentError:
            return False

    def save_data(self, game, gameport, name, map, maxplayers, players, bots, password):
        data = {}

        # save game name, ip address, query port
        data["game"], data["address"], data["port"] = game, self.address, gameport

        # save server name, map name, max players count
        data["name"], data["map"], data["maxplayers"] = name, map, maxplayers

        # save current players count, bots count
        data["players"], data["bots"], data["password"] = players, bots, password

        self.set_status("Online")

        with open(f'cache/{self.file_name}.json', "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)