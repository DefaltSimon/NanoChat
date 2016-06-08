"""Nano Python Client"""

__version__ = "0.3"
__author__ = "DefaltSimon"

import socket,sys

def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        print("Client disconnected.")
        return
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = excepthook

class PythonChat:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connected = []
    def connect(self,ip,port):
        try:
            self.sock.connect((ip,port))
            self.connected.append(ip)
        except ConnectionRefusedError:
            print("Client refused to connect.")
        except OSError:
            print("Cannot connect twice!")
    def closesocket(self):
        self.sock.close()
    def sendmsg(self,msg):
        self.sock.sendall(str(msg).encode("utf-8"))
    def getdata(self):
        data = self.sock.recv(4096)
        return data

def start():

    closed = False
    validresp = None
    chat = PythonChat()

    print("Nano Chat " + __version__ + "\n------------------")

    # One socket for one connection ONLY!
    #with open("friends.txt","r") as file:
    #    file = file.readlines()
    #    users = []
    #    for c, line in enumerate(file):
    #        if line.startswith("#"):
    #            continue
    #
    #        thing = line.strip("\n").split("::")
    #        host = thing[0]
    #        port = thing[1]
    #        alias = thing[2]
    #        users.append([host,port,alias])
    #    print(users)
    #
    #for host, port, alias in users:
    #    chat.connect(host,int(port))
    #    print("Connected to " + host + " (" + alias + ")")
    #print("Initialization complete.")

    print("What do you want to do? type help for a list of commands")
    while True:
        option = input(">")

        if option == "help":
            print("Commands: connect, send, close, chat, stop")

        elif option == "connect" or option == "cn":
            if closed is True:
                del chat
                chat = PythonChat()
            if chat.connected:
                print("You are already connected to one client. This version does not support multiple client connections.")
            try:
                ip = input("Host:")
                if not ip:
                    ip = "localhost"
                port = input("Port (default 420):")
                if not port:
                    port = 420
                if ip in chat.connected:
                    print("You are already connected to this ip.")
                    continue
                chat.connect(ip,int(port))
            except ValueError:
                print("Incorrect input")
            resp = bytes(chat.getdata()).decode("utf-8")

            #if resp.startswith("Nano Server") and resp.endswith("OK"):
            #    validresp = "Valid"
            #else:
            #    validresp = "Not valid"
            #
            #print("Response: " + resp + " (" + str(validresp) + ")")
            print("Connected to " + str(ip))

        elif option == "close":
            chat.closesocket()
            closed = True
            chat.connected = []
            print("Closed the connection.")

        elif option == "connections":
            print(chat.connected)

        elif option == "stop":
            print("Disconnecting from servers...")
            chat.closesocket()
            print("Done. Bye!")
            exit()

        elif str(option).startswith("chat"):
            if str(option)[len("chat"):] != "":
                msg = str(option)[len("chat")+1:]
            else:
                msg = input("Message:")
            chat.sendmsg(msg)
            print("msg: " + msg)

start()