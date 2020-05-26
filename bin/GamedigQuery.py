# original author: BrandonFL
# require gamedig: npm install -g gamedig

import platform
import subprocess
import json
import re

class GamedigQuery(object):
    def __init__(self, game, addr, port=27015):
        self.game, self.ip, self.port = game, addr, port

    def getInfo(self):
        try:
            process = subprocess.run(
                ['gamedig', '--type', str(self.game), '--host', str(self.ip), '--port', str(self.port)],
                stdout=subprocess.PIPE, shell=platform.system() == 'Windows' and True or False)
            output = process.stdout.decode('utf8')

            json_reader = json.loads(str(output).replace("b'", "").replace("\\n'", ""))

            if 'error' in json_reader:
                return False
            elif 'name' in json_reader:
                result = {}
                result['_engine_'] = 'Gamedig'

                result['Hostname'] = json_reader['name']
                if str(self.game) == 'fivem': # remove fivem server color code
                    result['Hostname'] = re.sub(r'\^[0-9]', '', result['Hostname'])

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
    gamedigQuery = GamedigQuery('fivem', '54.37.244.192', 30120)
    print(gamedigQuery.getInfo())