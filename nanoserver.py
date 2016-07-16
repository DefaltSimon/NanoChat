# coding=utf-8
"""Nano Python Server"""

__version__ = "0.4"
__author__ = "DefaltSimon"

import socket
import sys
import threading
import json
import configparser

from random import randint
from Crypto.Cipher import AES

def excepthook(exctype, value, traceback):  # Custom exception hook

    if exctype == ConnectionResetError:
        print("Client disconnected.")
        return

    else:
        sys.__excepthook__(exctype, value, traceback)  # If no filters are to be applied, apply default exception hook

sys.excepthook = excepthook  # Hook it!


# 'Constants'

PADDING = 16
KEY_LENGTH = 16
padchar = "="

hostd = ""  # Represents localhost
portd = 420  # Outgoing port
defclientportd = 421  # Incoming port

# Utilities
def pad(key):
    # Pads a string so it can be encrypted
    if len(key) == PADDING:
        return key

    else:
        fill = PADDING - len(key) % PADDING
        return key + padchar * fill

def gotmsg(user, content, to):
    if not content:
        return

    print("Message from " + user + " to " + str(to) + ": " + str(content))

def error(content):
    if not content:
        return

    print("[ERROR] {}".format(content))

# Exceptions
class InvalidParameters(Exception):
    def __init__(self, *args, **kwargs):
        pass

class PythonChat:
    def __init__(self,host,port):
        if not isinstance(host, str) or not isinstance(port, int):
            raise InvalidParameters

        self.users = {}
        self.ips = {}

        self.key = None  # 16-bit key
        self.encryption = None  # AES

        self.servername = ""
        self.password = ""

        self.pending = {}

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        self.sock.setblocking(1)

        self.sock.bind((host, port))
        self.sock.listen(5)
    def setservername(self,name):
        self.servername = str(name)

    def setpassword(self,password):
        self.password = str(password)

    def generatekey(self, length):
        key = ""
        for rn in range(length):
            # Random char 0 - 9
            key += str(randint(0, 9))

        if len(key) == length:
            self.key = key
            return key

        else:
            raise InvalidParameters


    def encrypt(self,content):

        if not self.encryption:
            self.setupenc()

        return self.encryption.encrypt(pad(str(content)))

    def setupenc(self):
        if not self.key:
            self.generatekey(KEY_LENGTH)

        if not self.encryption:
            self.encryption = AES.new(self.key)

    def verifyuser(self, username, addr):
        try:
            if self.ips[username] == addr:
                return True
            else:
                return False
        except KeyError:
            return False

    def start(self):

        while True:
            conn, addr = self.sock.accept()

            data = bytes(conn.recv(4096)).decode("utf-8")
            #print("Data: " + data)
            initial = json.loads(data)

            if initial["type"] == "initial":
                if self.password:
                    self.pending[str(addr[0])] = initial["username"]
                else:
                    self.users[str(addr[0])] = initial["username"]
                    self.ips[initial["username"]] = str(addr[0])

            else:
                print("Error: Not an initial connection")
                continue

            if self.password:
                raw = {
                    "type": "initialresponse",
                    "code":"OK","servername":self.servername,
                    "password":"required",
                    "key": self.key
                }

            else:
                raw = {"type": "initialresponse",
                       "code":"OK","servername":self.servername,
                       "key":self.key
                       }
            senc = json.dumps(raw).encode("utf-8")

            conn.send(senc)

            try:
                currentuser = str(self.users.get(addr[0]))
            except TypeError:
                currentuser = "error"

            if self.password:
                print("Requesting password from {} ({})".format(addr[0], initial["username"]))
            else:
                print("Connected from {} ({})".format(addr[0], currentuser))

            anotherthread = threading.Thread(target=self.waitformsg,args=[conn,addr])
            anotherthread.daemon = True
            anotherthread.start()
    def waitformsg(self, conn1, addr1):
        while True:

            try:
                demsg = bytes(conn1.recv(4096))

                if not demsg:
                    continue

                # Try to decrypt and/or decode
                demsg = json.loads(str(self.encryption.decrypt(demsg).decode("utf-8")).rstrip("="))

                username1 = str(demsg["username"])

                # Beacuse of multiple threads, this checks if the message received should even be processed
                if self.verifyuser(demsg["username"], addr1[0]) or (self.pending[addr1[0]] == username1):
                    sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    sock2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
                    sock2.setblocking(1)

                    sock3 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    sock3.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
                    sock3.setblocking(1)

                    if demsg["type"] == "getclients":
                        sock2.connect((addr1[0],defclientportd))
                        raw = self.encrypt(json.dumps({"type":"clients",
                                          "content":self.users}))
                        sock2.send(raw)

                        print("{} requested clients list.".format(demsg["username"]))

                    elif demsg["type"] == "connectiontest":
                        sock2.connect((addr1[0],defclientportd))
                        raw = self.encrypt(json.dumps({"type":"connectiontest",
                                "content":"ok"}))
                        sock2.send(raw)
                        print("{} tested connection.".format(demsg["username"]))

                    elif demsg["type"] == "disconnect":
                        print("{} ({})  disconnected.".format(addr1[0], self.users[addr1[0]]))

                        try:
                            self.users.pop(str(addr1[0]))
                        except KeyError:
                            pass

                        return  # Exits this thread (representing a connection to a client)

                    elif demsg["type"] == "password":
                        if self.pending[addr1[0]] == username1:
                            # Password check

                            if self.password == demsg["content"]:
                                raw = {"type":"passwordresponse",
                                       "wascorrect":True,
                                       "key":self.key
                                       }

                                self.users[str(addr1[0])] = username1
                                self.ips[username1] = str(addr1[0])

                                quit = False
                                print("Connected from " + str(addr1[0]) + " (" + username1 + ")")

                            else:
                                raw = {"type":"passwordresponse",
                                       "wascorrect":False
                                       }

                                quit = True
                                print(str(addr1[0]) + " (" + username1 + ") failed to connect: password incorrect")

                            senc = self.encrypt(json.dumps(raw))
                            sock2.connect((addr1[0],defclientportd))
                            sock2.send(senc)

                            if quit:
                                return  # Exits this thread (representing a connection to a client)

                    if "sendto" in demsg:

                        try:
                            gotmsg(self.users.get(addr1[0]),demsg["content"],demsg["sendto"])

                        except TypeError:
                            gotmsg("somebody",demsg["content"],demsg["sendto"])

                        ipadd = self.ips.get(str(demsg["sendto"]))

                        if ipadd is None:
                            sock2.connect((addr1[0], defclientportd))
                            raw = self.encrypt(json.dumps({"type":"failedmsg",
                                              "failedto":demsg["sendto"],
                                              "reason":"No user with that name"}))
                            sock2.send(raw)

                        else:
                            sock3.connect((addr1[0], defclientportd))
                            raw = self.encrypt(json.dumps({"type":"successfulmsg"}))
                            sock3.send(raw)

                            sock2.connect((ipadd, defclientportd))
                            raw = self.encrypt(json.dumps({"type":"msg",
                                              "from":str(demsg["username"]),
                                              "content":str(demsg["content"])}))
                            sock2.send(raw)


            except ConnectionResetError:
                try:
                    usern = str(self.users[addr1[0]])
                    print("{} ({}) disconnected.".format(usern, addr1[0]))
                except KeyError:
                    error("Could not find a connected client's username.")
                    print("{} disconnected.".format(addr1[0]))

                try:
                    self.users.pop(str(addr1[0]))
                except KeyError:
                    pass

                return

    def closesocket(self):
        self.sock.close()

length = len("Nano Chat Server "  + __version__)
print("Nano Chat Server" + __version__ + "\n" + str( "-" * length))  # Banner

config = configparser.ConfigParser()
config.read("serversettings.ini")

usepass = config.getboolean("Settings","usepassword")
password = config.get("Settings","password")
usename = config.getboolean("Name","usename")
servernam = config.get("Name","servername")

chat = PythonChat(hostd, portd)

if usepass:
    chat.setpassword(password)
    print("Password: " + str(password))

if usename:
    chat.setservername(servernam)
    print("Server name: " + str(servernam))

else:
    servernam = input("Server name: ")
    chat.setservername(str(servernam))

generatedkey = chat.generatekey(KEY_LENGTH)  # Generates a 16-bit key

print("Encryption key: " + str(generatedkey))

print(str( "-" * len("Server Name: " + str(servernam))))

chat.setupenc()  # Sets up encryption (generates a 16-bit key if not done so and creates AESCipher)

chat.start()  # Starts the infinite loop