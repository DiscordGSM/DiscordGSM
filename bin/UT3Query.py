# more info: https://wiki.unrealadmin.org/UT3_query_protocol
# author: TatLead

import socket
import time
import struct
import sys
import re

class UT3Query(object):
    def __init__(self, addr, port=19132, timeout=5.0):
        self.ip, self.port, self.timeout = socket.gethostbyname(addr), port, timeout
        self.sock = False

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = False

    def connect(self):
        self.disconnect()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ip, self.port))

    def getInfo(self):
        self.connect()

        # initial request  
        try:
            self.sock.send(b'\xFE\xFD\x09\x10\x20\x30\x40')
            response = self.sock.recv(4096)
        except Exception as e:
            print(e)
            return False

        # second request with token
        try:
            token = int(response[5:].decode('ascii').strip('\x00')).to_bytes(4, byteorder='big', signed=True)
            self.sock.send(b'\xFE\xFD\x00\x10\x20\x30\x40'+token+b'\xFF\xFF\xFF\x01')
            response = self.sock.recv(4096)
        except Exception as e:
            print(e)
            return False

        try:
            response = response[16:].decode('unicode_escape').split('\x00\x00\x01player_\x00\x00')
            response = re.sub(r'§.', '', response[0]).replace('\n', ' ') # remove color and next line
            #print(response) # useful output
            kv = response.split('\x00')
            result = {}
            for i in range(0, len(kv), 2):
                result[kv[i]] = kv[i+1]
            return result
        except Exception as e:
            print(e)
            return False

        return False

if __name__ == '__main__':
    ut3Query = UT3Query('145.239.205.107', 25565)
    print(ut3Query.getInfo())