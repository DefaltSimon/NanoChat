"""Nano Python Client"""

__version__ = "0.3.4"
__author__ = "DefaltSimon"

import socket,sys,json,threading,time

hostm, portm = "",421

# Outgoing port is usually 420 (server default)
# Incoming is 421

listenerlock = False
isclosing = False

def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        global isclosing
        if not isclosing:
            print("Connection to server could not be established or was closed.")
        else:
            isclosing = False
        return
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = excepthook

class PythonChat:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connected = ""
        self.servername = ""
        self.username = ""

        self.connectiontest = False
        self.connectiontime = 0

        self.passwordcorrect = False
    def setusername(self,username):
        self.username = str(username)
    def connect(self,ip,port):
        try:
            self.sock.settimeout(2)
            try:
                self.sock.connect((ip,port))
            except OSError:
                print("Server could not be reached.")
                return False
            araw = ({"type":"initial","username":self.username})
            self.sock.send(json.dumps(araw).encode("utf-8"))
            self.connected = str(ip)
            return True
        except ConnectionRefusedError:
            print("Client refused to connect.")
            return False
    def closesocket(self):
        global isclosing
        isclosing = True
        raw = ({"type":"disconnect","username":self.username})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
        time.sleep(0.1)
        self.sock.close()
    def listener(self):
        print("started")

        sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        sock2.setblocking(1)

        sock2.bind((hostm, portm))
        sock2.listen(3)

        while True:
            conn, addr = sock2.accept()
            data = json.loads(bytes(conn.recv(4096)).decode("utf-8"))
            #print(data)

            msgtype = data["type"]
            # Resolves type
            if msgtype == "msg":
                author = data["from"]
                content = data["content"]
                print("Message from " + author +": " + content)
            elif msgtype == "clients":
                clients = data["content"]
                compiledclients = ""
                for item in clients.items():
                    compiledclients  += item[0] + " : " + item[1]
                    compiledclients += "\n"

                print("Clients connected to main server: \n" + str(compiledclients).strip("\n"))
            elif msgtype == "connectiontest":
                if data["content"] == "ok":
                    self.connectiontest = True
                else:
                    self.connectiontest = True
            elif msgtype == "passwordresponse":
                if data["wascorrect"]:
                    self.passwordcorrect = True
                else:
                    self.passwordcorrect = False
    def sendmsg(self,loc,msg):
        raw = ({"type":"msg","content":str(msg),"username":self.username,"sendto":str(loc)})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
    def sendpass(self,passw):
        raw = ({"type":"password","content":str(passw),"username":self.username})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
    def getclients(self):
        raw = ({"type":"getclients","username":self.username})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
        # listener catches the answer

    def testconnection(self):
        raw = ({"type":"connectiontest","username":self.username})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)

        tries = 5
        count = 1
        print("Testing..",end="")
        while tries != 0:
            if self.connectiontest is not False:
                print("connection ok")
                self.connectiontest = False
                return
            else:
                print(".",end="")
            count += 1
            time.sleep(0.2)
        print("no connection")

    def getdata(self):
        if not self.connected:
            return
        try:
            data = json.loads(bytes(self.sock.recv(4096)).decode("utf-8"))
            return data
        except OSError:
            print("Socket not connected, OSError.")

def start():

    closed = False
    print("Nano Chat " + __version__ + "\n------------------")

    chat = PythonChat()

    print("Starting listener....",end="")
    thr = threading.Thread(target=chat.listener)
    thr.daemon = True
    thr.start()

    username = str(input("Username:"))
    chat.setusername(username)

    print("What do you want to do? type help for a list of commands")
    while True:
        option = input(">")

        if option == "help":
            print("Commands: connect, connections, clients, close, chat, test, stop")

        elif option == "aliases":
            aliases = "Aliases: connect - 'cn', chat - 'c', clients - 'users'"
            print(aliases)

        elif option == "connect" or option == "cn":
            if closed is True:
                del chat
                chat = PythonChat()
                chat.setusername(username)
            if chat.connected:
                print("You are already connected to one server. Current version does not support multiple client-to-server connections.")
                continue
            ip = None
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
                eins = chat.connect(ip,int(port))
                if not eins:
                    print("quitting")
                    continue
            except ValueError:
                print("Incorrect input")
                continue
            try:
                resp = chat.getdata()
                chat.servername = resp["servername"]
                try:
                    passwn = bool(resp["password"] == "required")
                except KeyError:
                    passwn = False
                if passwn:
                    password = input("Password: ")
                    chat.sendpass(password)
                    c = 5
                    isk = False
                    while c >= 0:
                        if chat.passwordcorrect:
                            print("Correct!")
                            isk = True
                            break
                        else:
                            time.sleep(0.1)
                            c -= 1
                else:
                    isk = True
                if isk:
                    if resp["code"] == "OK":
                        validresp = "ok response"
                    else:
                        validresp = "incorrect response?!"
                    print("Connected to " + str(ip) + " (" + chat.servername + ")..." + validresp)
                else:
                    print("Incorrect password, try again")
                    continue
            except:
                print("No data in response.")

            #print("Response: " + resp + " (" + str(validresp) + ")")

        elif option == "close":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            chat.closesocket()
            closed = True
            print(chat.connected)
            print("Closed the connection to " + chat.connected)
            chat.connected = []

        elif option == "connections":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            clients = chat.connected
            print(clients + " ({})".format(chat.servername))

        elif option == "test" or option == "test connections":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            chat.testconnection()

            time.sleep(0.2)

        elif option == "clients" or option == "users":
            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            chat.getclients()

            time.sleep(0.2)

        elif option == "stop":
            print("Disconnecting from servers...",end="")
            chat.closesocket()
            print("done. Cya!")
            exit()

        elif str(option).startswith("chat") or str(option) == "c":
            #if str(option)[len("chat"):] != "":
            #    msg = str(option)[len("chat")+1:]
            #else:

            if not chat.connected:
                print("You are not connected to a server. Use 'connect' to connect to a server")
                continue
            msg = input("Message:")
            loca = input("Send to:")
            chat.sendmsg(loca,msg)
            print("Sent msg: " + msg)

            time.sleep(0.2)

start()