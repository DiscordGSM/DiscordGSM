# -*- coding: utf-8 -*-

# original author: Dasister
# modified by: Halreis, TatLead
# modifications: omitted useless functions, optimized the code

A2S_INFO = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
A2S_PLAYERS = b'\xFF\xFF\xFF\xFF\x55'
A2S_RULES = b'\xFF\xFF\xFF\xFF\x56'

S2A_INFO_SOURCE = chr(0x49)
S2A_INFO_GOLDSRC = chr(0x6D)

import socket
import time
import struct
import sys


class SourceQuery(object):
    def __init__(self, address, port=27015, timeout=5.0):
        self.ip, self.port, self.timeout = socket.gethostbyname(address), port, timeout
        self.sock = False

    def getInfo(self):
        self.connect()
        self.sock.send(A2S_INFO)
        try:
            data = self.sock.recv(4096)
        except:
            return False

        header, data = self.getByte(data[4:])

        # (12/8/2021) Changes to server browser packets in latest Steam client
        # https://steamcommunity.com/discussions/forum/14/2974028351344359625/
        if chr(header) == 'A':
            self.sock.send(A2S_INFO + data)
            data = self.sock.recv(4096)
            header, data = self.getByte(data[4:])

        result = {}

        if chr(header) == S2A_INFO_SOURCE:
            result['_engine_'] = 'Source'

            result['Protocol'], data = self.getByte(data)
            result['Hostname'], data = self.getString(data)
            result['Map'], data = self.getString(data)
            result['GameDir'], data = self.getString(data)
            result['GameDesc'], data = self.getString(data)
            result['AppID'], data = self.getShort(data)
            result['Players'], data = self.getByte(data)
            result['MaxPlayers'], data = self.getByte(data)
            result['Bots'], data = self.getByte(data)
            dedicated, data = self.getByte(data)
            if chr(dedicated) == 'd':
                result['Dedicated'] = 'Dedicated'
            elif dedicated == 'l':
                result['Dedicated'] = 'Listen'
            else:
                result['Dedicated'] = 'SourceTV'

            os, data = self.getByte(data)
            if chr(os) == 'w':
                result['OS'] = 'Windows'
            elif chr(os) in ('m', 'o'):
                result['OS'] = 'Mac'
            else:
                result['OS'] = 'Linux'
            result['Password'], data = self.getByte(data)
            result['Secure'], data = self.getByte(data)
            if result['AppID'] == 2400:  # The Ship server
                result['GameMode'], data = self.getByte(data)
                result['WitnessCount'], data = self.getByte(data)
                result['WitnessTime'], data = self.getByte(data)
            result['Version'], data = self.getString(data)
            edf, data = self.getByte(data)
            try:
                if edf & 0x80:
                    result['GamePort'], data = self.getShort(data)
                if edf & 0x10:
                    result['SteamID'], data = self.getLongLong(data)
                if edf & 0x40:
                    result['SpecPort'], data = self.getShort(data)
                    result['SpecName'], data = self.getString(data)
                if edf & 0x10:
                    result['Tags'], data = self.getString(data)

                    # mordhau fix
                    if result['GameDesc'] == 'Mordhau':
                        result['AppID'], data = self.getLongLong(data)
                        tags = str(result['Tags']).split(',')
                        for tag in tags:
                            if tag[:2] == 'B:':
                                result['Players'] = tag[2:]
                                break
            except:
                pass
        elif chr(header) == S2A_INFO_GOLDSRC:
            result['_engine_'] = 'GoldSRC'

            result['GameIP'], data = self.getString(data)
            result['Hostname'], data = self.getString(data)
            result['Map'], data = self.getString(data)
            result['GameDir'], data = self.getString(data)
            result['GameDesc'], data = self.getString(data)
            result['Players'], data = self.getByte(data)
            result['MaxPlayers'], data = self.getByte(data)
            result['Version'], data = self.getByte(data)
            dedicated, data = self.getByte(data)
            if chr(dedicated) == 'd':
                result['Dedicated'] = 'Dedicated'
            elif dedicated == 'l':
                result['Dedicated'] = 'Listen'
            else:
                result['Dedicated'] = 'HLTV'
            os, data = self.getByte(data)
            if chr(os) == 'w':
                result['OS'] = 'Windows'
            else:
                result['OS'] = 'Linux'
            result['Password'], data = self.getByte(data)
            result['IsMod'], data = self.getByte(data)
            if result['IsMod']:
                result['URLInfo'], data = self.getString(data)
                result['URLDownload'], data = self.getString(data)
                data = self.getByte(data)[1]  # NULL-Byte
                result['ModVersion'], data = self.getLong(data)
                result['ModSize'], data = self.getLong(data)
                result['ServerOnly'], data = self.getByte(data)
                result['ClientDLL'], data = self.getByte(data)
            result['Secure'], data = self.getByte(data)
            result['Bots'], data = self.getByte(data)

        return result

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = False

    def connect(self):
        self.disconnect()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ip, self.port))

    # WORKER FUNCTIONS #

    def getByte(self, data):
        return data[0], data[1:]

    def getShort(self, data):
        return struct.unpack('<h', data[0:2])[0], data[2:]

    def getLong(self, data):
        return struct.unpack('<l', data[0:4])[0], data[4:]

    def getLongLong(self, data):
        return struct.unpack('<Q', data[0:8])[0], data[8:]

    def getFloat(self, data):
        return struct.unpack('<f', data[0:4])[0], data[4:]

    def getString(self, data):
        s = data[0:].split(b'\x00')[0]
        return str(s, encoding='utf-8', errors='ignore'), data[len(s) + 1:]


# Debug
if __name__ == '__main__':
    sourceQuery = SourceQuery('168.119.39.60', 27013)
    print(sourceQuery.getInfo())
