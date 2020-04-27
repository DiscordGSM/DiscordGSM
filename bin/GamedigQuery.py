# original author: BrandonFL
# require gamedig: npm install -g gamedig

import subprocess
import json

class GamedigQuery(object):
    def __init__(self, game, addr, port=27015):
        self.game, self.ip, self.port = game, addr, port

    def getInfo(self):
        try:
            process = subprocess.Popen(
                ['gamedig', '--type', str(self.game), '--host', str(self.ip), '--port', str(self.port)],
                shell=True, stdout=subprocess.PIPE)
            output = process.stdout.read()

            json_reader = json.loads(str(output).replace("b'", "").replace("\\n'", ""))

            if 'error' in json_reader:
                return False
            elif 'name' in json_reader:
                result = {}
                result['_engine_'] = 'Gamedig'

                result['Hostname'] = json_reader['name']
                result['Map'] = json_reader['map']
                result['Players'] = len(json_reader['players'])
                result['MaxPlayers'] = int(json_reader['maxplayers'])
                result['Bots'] = len(json_reader['bots'])
                result['Password'] = json_reader['password']

                if 'secure' in json_reader['raw']:
                    result['Secure'] = json_reader['raw']['secure']

                if 'version' in json_reader['raw']:
                    result['Version'] = json_reader['raw']['version']

                return result
            else:
                return False
        except:
            return False


if __name__ == '__main__':
    gamedigQuery = GamedigQuery("wolfensteinet", "127.0.0.1", 27960)
    print(gamedigQuery.getInfo())