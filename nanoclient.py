"""Nano Python Client"""

__version__ = "0.3.2"
__author__ = "DefaltSimon"

import socket,sys,json,threading,time

hostm, portm = "",421

listenerlock = False

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
        self.username = ""

        self.listenerlock = False
    def setusername(self,username):
        self.username = str(username)
    def connect(self,ip,port):
        try:
            self.sock.connect((ip,port))
            araw = ({"type":"initial","username":self.username})
            self.sock.send(json.dumps(araw).encode("utf-8"))
            self.connected.append(ip)
        except ConnectionRefusedError:
            print("Client refused to connect.")
        #except OSError:
        #    print("Cannot connect twice!")
    def closesocket(self):
        self.sock.close()
    def listener(self):
        print("started")

        sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        sock2.setblocking(1)

        sock2.bind((hostm, portm))
        sock2.listen()

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
                print("Clients connected to main server: " + str(clients))
                global listenerlock
                listenerlock = False
    def sendmsg(self,loc,msg):
        raw = ({"type":"msg","content":str(msg),"username":self.username,"sendto":str(loc)})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
    def getclients(self):
        raw = ({"type":"getclients","username":self.username})
        senc = json.dumps(raw).encode("utf-8")
        self.sock.send(senc)
        # listener catches the answer
        global listenerlock
        listenerlock = True
    def getdata(self):
        try:
            data = self.sock.recv(4096)
            return data
        except OSError:
            print("Socket not connected, OSError.")

def start():

    closed = False
    validresp = None
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
            print("Commands: connect, connections, clients, close, chat, stop")

        elif option == "connect" or option == "cn":
            if closed is True:
                del chat
                chat = PythonChat()
                chat.setusername(username)
            if chat.connected:
                print("You are already connected to one server. Current version does not support multiple client-to-server connections.")
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
                chat.connect(ip,int(port))
            except ValueError:
                print("Incorrect input")
            try:
                resp = bytes(chat.getdata()).decode("utf-8")
                if resp.startswith("Nano Server") and resp.endswith("OK"):
                    validresp = "ok response"
                else:
                    validresp = "not ok response?!"
                print("Connected to " + str(ip) + " (" + validresp + ")")
            except:
                print("No data in response.")

            #print("Response: " + resp + " (" + str(validresp) + ")")

        elif option == "close":
            chat.closesocket()
            closed = True
            chat.connected = []
            print("Closed the connection.")

        elif option == "connections":
            print(chat.connected)

        elif option == "clients" or option == "users":
            chat.getclients()

            time.sleep(0.2)

        elif option == "stop":
            print("Disconnecting from servers...")
            chat.closesocket()
            print("Done. Bye!")
            exit()

        elif str(option).startswith("chat") or str(option) == "c":
            #if str(option)[len("chat"):] != "":
            #    msg = str(option)[len("chat")+1:]
            #else:
            msg = input("Message:")
            loca = input("Send to:")
            chat.sendmsg(loca,msg)
            print("Sent msg: " + msg)

            time.sleep(0.2)

start()