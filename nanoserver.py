"""Nano Python Server"""

__version__ = "0.3.6dev"
__author__ = "DefaltSimon"

import socket,sys,threading,json,configparser

def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        print("Client disconnected.")
        return
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = excepthook

# Outgoing
hostd, portd = "",420
# Incoming
defclientportd = 421

def gotmsg(user,content,to):
    if not content:
        content = None
    print("Message from " + user + " to " + str(to) + ": " + str(content))

def clientsrequested(user):
    print("{} requested client list.".format(str(user)))

class PythonChat:
    def __init__(self,host,port):
        self.wasconnected = []
        self.users = {}
        self.ips = {}

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
    def waitforfirstconn(self):
        while True:
            conn, addr = self.sock.accept()
            self.wasconnected.append(str(addr[0]))

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
                    "password":"required"
                }
            else:
                raw = {"type": "initialresponse",
                       "code":"OK","servername":self.servername
                       }
            senc = json.dumps(raw).encode("utf-8")
            #conn.send("Nano Server 0.1 OK".encode("utf-8"))
            conn.send(senc)
            try:
                currentuser = str(self.users.get(addr[0]))
            except TypeError:
                currentuser = "error"
            if self.password:
                print("Requesting password from " + str(addr[0]) + " (" + initial["username"] + ")")
            else:
                print("Connected from " + str(addr[0]) + " (" + currentuser + ")")
            anotherthread = threading.Thread(target=self.waitformsg,args=[conn,addr])
            anotherthread.daemon = True
            anotherthread.start()
    def waitformsg(self,conn1, addr1):
        while True:
            demsg = None
            try:
                msg = bytes(conn1.recv(4096)).decode("utf-8")
                if msg:
                    demsg = json.loads(msg)
                else:
                    continue
                username1 = str(demsg["username"])

                # Beacuse of multiple threads, this checks if the message received should even be processed
                shouldgoon = False
                try:
                    shouldgoon = bool(self.users[addr1[0]] == username1)
                except KeyError:
                    shouldgoon = bool(self.pending[addr1[0]] == username1)
                if shouldgoon:
                    sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    sock2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
                    sock2.setblocking(1)

                    sock3 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    sock3.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
                    sock3.setblocking(1)

                    if demsg["type"] == "getclients":
                        sock2.connect((addr1[0],defclientportd))
                        raw = json.dumps({"type":"clients",
                                          "content":self.users}).encode("utf-8")
                        sock2.send(raw)
                        clientsrequested(demsg["username"])
                    elif demsg["type"] == "connectiontest":
                        sock2.connect((addr1[0],defclientportd))
                        raw = ({"type":"connectiontest",
                                "content":"ok"})
                        senc = json.dumps(raw).encode("utf-8")
                        sock2.send(senc)
                        print("{} tested connection.".format(demsg["username"]))
                    elif demsg["type"] == "disconnect":
                        print("{} ({})  disconnected.".format(str(addr1[0]),str(self.users[addr1[0]])))
                        try:
                            self.users.pop(str(addr1[0]))
                        except KeyError:
                            pass
                        return
                    elif demsg["type"] == "password":
                        if self.pending[addr1[0]] == username1:
                            # Password check
                            if self.password == demsg["content"]:
                                raw = {"type":"passwordresponse",
                                       "wascorrect":True
                                       }

                                self.users[str(addr1[0])] = username1
                                self.ips[username1] = str(addr1[0])
                                shouldquit = False
                                print("Connected from " + str(addr1[0]) + " (" + username1 + ")")
                            else:
                                raw = {"type":"passwordresponse",
                                       "wascorrect":False
                                       }
                                shouldquit = True
                                print(str(addr1[0]) + " (" + username1 + ") failed to connect: password incorrect")

                            senc = json.dumps(raw).encode("utf-8")
                            sock2.connect((addr1[0],defclientportd))
                            sock2.send(senc)

                            if shouldquit:
                                return

                    if "sendto" in demsg:
                        try:
                            gotmsg(self.users.get(addr1[0]),demsg["content"],demsg["sendto"])
                        except TypeError:
                            gotmsg("somebody",demsg["content"],demsg["sendto"])

                        ipadd = self.ips.get(str(demsg["sendto"]))
                        if ipadd is None:
                            sock2.connect((addr1[0],defclientportd))
                            raw = json.dumps({"type":"failedmsg",
                                              "failedto":demsg["sendto"],
                                              "reason":"No user with that name"}).encode("utf-8")
                            sock2.send(raw)
                        else:
                            sock3.connect((addr1[0],defclientportd))
                            raw = json.dumps({"type":"successfulmsg"}).encode("utf-8")
                            sock3.send(raw)

                            sock2.connect((ipadd,defclientportd))
                            raw = json.dumps({"type":"msg",
                                              "from":str(demsg["username"]),
                                              "content":str(demsg["content"])}).encode("utf-8")
                            sock2.send(raw)


            except ConnectionResetError:
                try:
                    usern = str(self.users[addr1[0]])
                except KeyError:
                    usern = "None"
                print("{} ({}) disconnected.".format(str(addr1[0]),usern))
                try:
                    self.users.pop(str(addr1[0]))
                except KeyError:
                    pass
                return
    def closesocket(self):
        self.sock.close()
    def getdata(self):
        conn, addr = self.sock.accept()
        data = conn.recv(4096)
        print(data)

length = len("Nano Chat Server "  + __version__)
print("Nano Chat Server" + __version__ + "\n" + str( "-" * length))

# todo Feature: autoconnect from a text file?
#try:
#    with open("friends.txt","r") as file:
#        file = file.readlines()
#        users = {}
#        for c, line in enumerate(file):
#            if line.startswith("#"):
#                continue
#            thing = line.strip("\n").split("::")
#            host1 = thing[0]
#            alias = thing[1]
#            users[host1] = alias
#except IndexError:
#    print("Error while parsing friends.txt, quiting.")
#    exit()

config = configparser.ConfigParser()
config.read("serversettings.ini")
usepass = config.getboolean("Settings","usepassword")
password = config.get("Settings","password")
usename = config.getboolean("Name","usename")
servernam = config.get("Name","servername")

chat = PythonChat(hostd,portd)

if usepass:
    chat.setpassword(password)
    print("Password: " + str(password))

if usename:
    chat.setservername(servernam)
    print("Server name: " + str(servernam))
else:
    servernam = input("Server name: ")
    chat.setservername(str(servernam))
print(str( "-" * len("Server Name: " + str(servernam))))

chat.waitforfirstconn()