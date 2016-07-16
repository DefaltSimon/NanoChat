# coding=utf-8
"""Nano Python Client"""

__version__ = "0.4"
__author__ = "DefaltSimon"

import socket, sys, json, threading, time
from Crypto.Cipher import AES

def pad(key):

    if len(key) == PADDING:
        return key

    else:
        fill = PADDING - len(key) % PADDING
        return key + padchar * fill

# 'Constants'

PADDING = 16
padchar = "="
hostm = ""
portm = 421

# Outgoing port is usually 420 (server default)
# Incoming is 421

isclosing = False


def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        global isclosing
        if not isclosing:
            print("Connection to server could not be established or was closed.")
        else:
            isclosing = False
    else:
        sys.__excepthook__(exctype, value, traceback)


sys.excepthook = excepthook


class NoEncryptytionKey(Exception):
    def __init__(self):
        return

class NanoChat:
    """
    The main Nano Chat class, featuring the main functions.
    """
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = ""
        self.servername = ""
        self.username = ""

        self.connectiontest = False
        self.connectiontime = 0

        self.passwordcorrect = False

        self.listenerlock = False
        self.msgsent = False
        self.reason = ""

        self.enckey = None
        self.encryption = None
    def setusername(self, username):
        self.username = str(username)

    def setenckey(self,key):
        self.enckey = pad(key)

        return self.enckey

    def encrypt(self,content):

        if not self.encryption:
            self.encryption = AES.new(self.enckey)

        if not self.enckey:
            raise NoEncryptytionKey

        encrypted = self.encryption.encrypt(pad(str(content)))

        return encrypted

    def connect(self, ip, port):
        try:
            self.sock.settimeout(2)

            try:
                self.sock.connect((ip, port))
                araw = ({"type": "initial", "username": self.username})
                self.sock.send(json.dumps(araw).encode("utf-8"))
                self.connected = str(ip)

            except OSError as err:
                print("Server could not be reached: " + str(err))
                self.connected = ""
                return False
            return True

        except ConnectionRefusedError:
            print("Client refused to connect.")
            return False

    def closesocket(self):
        try:
            global isclosing
            isclosing = True

            raw = ({"type": "disconnect", "username": self.username})
            senc = self.encrypt(json.dumps(raw))
            self.sock.send(senc)
            time.sleep(0.1)
            self.sock.close()
        except OSError:
            pass  # Ignore if the socket is already closed

    def Lock(self):
        self.listenerlock = True

    def listener(self):
        print("started")

        # Listening socket, running in a thread
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock2.setblocking(1)

        sock2.bind((hostm, portm))
        sock2.listen(3)

        while True:

            # Blocking, waits for a connection
            conn, addr = sock2.accept()

            self.listenerlock = True
            try:

                # Decodes, loads into a dictionary
                data = bytes(conn.recv(4096))

                # Try to decrypt and/or decode
                #try:
                #    data = json.loads(data.decode("utf-8"))
                #except UnicodeDecodeError or json.JSONDecodeError:
                data = json.loads(str(self.encryption.decrypt(data).decode("utf-8")).rstrip("="))

                msgtype = data["type"]

                # Resolves type
                if msgtype == "successfulmsg":  # prints Sent msg: content before Message from user: content if you send a message to yourself
                    self.msgsent = True

                elif msgtype == "msg":
                    author = data["from"]
                    content = data["content"]
                    print("Message from " + author + ": " + content)

                elif msgtype == "clients":
                    clients = data["content"]
                    compiledclients = ""
                    for item in clients.items():
                        compiledclients += item[0] + " : " + item[1]
                        compiledclients += "\n"
                    print("\nClients connected to main server: \n" + str(compiledclients).strip("\n"))

                elif msgtype == "connectiontest":
                    if data["content"] == "ok":
                        self.connectiontest = True
                    else:
                        self.connectiontest = True

                elif msgtype == "passwordresponse":
                    # Parses encryption key

                    # self.setenckey(data["key"])

                    if data["wascorrect"]:
                        self.passwordcorrect = True
                    else:
                        self.passwordcorrect = False

                elif msgtype == "failedmsg":
                    self.msgsent = False
                    self.reason = data["reason"]

                self.listenerlock = False

            finally:
                self.listenerlock = False

    def sendmsg(self, loc, msg):
        """Normal message"""
        raw = ({"type": "msg", "content": str(msg), "username": self.username, "sendto": str(loc)})
        senc = self.encrypt(json.dumps(raw))
        self.sock.settimeout(3)
        self.sock.send(senc)
        self.listenerlock = True

    def sendpass(self, passw):
        """Response with the password to finalize connecting"""
        raw = ({"type": "password", "content": str(passw), "username": self.username})
        senc = self.encrypt(json.dumps(raw))
        self.sock.send(senc)
        # self.listenerlock = True

    def getclients(self):
        """Requests clients. Response is caught by listener function"""
        raw = ({"type": "getclients", "username": self.username})
        senc = self.encrypt(json.dumps(raw))
        self.sock.send(senc)

    def testconnection(self):
        """Tests for connection/correct port forwarding. Response is caught by listener function"""
        raw = ({"type": "connectiontest", "username": self.username})
        senc = self.encrypt(json.dumps(raw))
        self.sock.send(senc)

        tries = 5
        count = 0
        print("Testing..", end="")
        while tries != 0:

            if self.connectiontest is not False:
                print("connection ok")
                self.connectiontest = False
                return
            else:
                print(".", end="")

            count += 1
            time.sleep(0.2)
        print("no connection or ping above 1s.")

    def getdata(self):
        if not self.connected:
            return

        data = bytes(self.sock.recv(4096))

        # Try to decrypt and/or decode
        try:
            data = json.loads(data.decode("utf-8"))
        except UnicodeDecodeError:
            data = json.loads(str(self.encryption.decrypt(data).decode("utf-8")).rstrip("="))


        return data

def start():
    length = len("Nano Chat " + __version__)
    print("Nano Chat " + __version__ + "\n" + str("-" * length))

    chat = NanoChat()

    print("Starting listener....", end="")
    thr = threading.Thread(target=chat.listener)
    thr.daemon = True
    thr.start()

    username = str(input("Username:"))
    chat.setusername(username)

    print("What do you want to do? type help for a list of commands")
    while True:
        option = input(">")

        if option == "help":
            print("Commands: connect, connection, clients, close, chat, test, stop")

        elif option == "aliases":
            aliases = "Aliases: connect - 'cn', chat - 'c', clients - 'users', connection - 'server', close - 'disconnect','dc', stop - 'exit'"
            print(aliases)

        elif option == "connect" or option == "cn":

            if chat.connected:
                print("You are already connected to one server. Current version does not support multiple client-to-server connections.")
                continue

            ip = None

            try:
                ip = str(input("Host:"))
                if not ip:
                    ip = "localhost"

                port = input("Port (default 420):")
                if not port:
                    port = 420

                else:
                    try:
                        port = int(port)
                    except ValueError:
                        print("Invalid port.")
                        continue

                if port == 421:
                    print("Port 421 not allowed, reverting to 420...")
                    port = 420
                if ip in chat.connected:
                    print("You are already connected to this ip.")
                    continue

                cn = chat.connect(ip, port)
                if not cn:
                    continue

            except ValueError as err:
                print("Incorrect input" + str(err))
                continue

            try:
                resp = chat.getdata()
                chat.servername = resp["servername"]

                chat.setenckey(str(resp["key"]).rstrip("="))
                try:
                    passwn = bool(resp["password"] == "required")
                except KeyError:
                    passwn = False

                if passwn:  # Request password from the user if the server has it
                    password = input("Password: ")
                    chat.sendpass(password)

                    chat.Lock()  # Employ the listener lock
                    isk = False

                    while chat.listenerlock:
                        time.sleep(0.1)
                    if chat.passwordcorrect:
                        print("Correct!")
                        isk = True

                else:
                    isk = True

                if isk:

                    if resp["code"] == "OK":
                        validresp = "response ok"
                    else:
                        validresp = "response incorrect?!"
                    print("Connected to " + str(ip) + " (" + chat.servername + ")..." + validresp)

                else:
                    print("Incorrect password, try again")

                    # Reinitializes the whole NanoChat class to avoid problems.
                    chat.__init__()
                    chat.setusername(username)
                    continue
            except:
                print("No data in response.")

        elif option == "close" or option == "disconnect" or option == "dc":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue

            chat.closesocket()
            print("Disconnected from " + chat.connected)

            chat.__init__()
            chat.setusername(username)

        elif option == "connection" or option == "server":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue

            clients = chat.connected
            print("Server IP: " + clients + "\nName: {}".format(chat.servername))

        elif option == "test" or option == "test connections":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue

            chat.testconnection()

            while chat.listenerlock:
                time.sleep(0.1)

        elif option == "clients" or option == "users":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            chat.getclients()

            while chat.listenerlock:
                time.sleep(0.1)

        elif option == "stop" or option == "exit":
            print("Disconnecting from servers...", end="")
            chat.closesocket()
            print("done. Cya!")
            exit()

        elif str(option).startswith("chat") or str(option) == "c":

            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue

            loca = input("Send to:")
            msg = input("Message:")

            chat.sendmsg(loca, msg)

            while chat.listenerlock:
                time.sleep(0.1)

            if chat.msgsent:
                print("Sent msg: " + msg)
            else:
                print("Failed to send message ({})".format(str(chat.reason)))
                chat.reason = ""


start()
