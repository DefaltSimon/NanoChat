"""Nano Python Server"""

__version__ = "0.3"
__author__ = "DefaltSimon"

import socket,sys,threading

def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        print("Client disconnected.")
        return
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = excepthook

hostd, portd = "",420

def gotmsg(user,content):
    if not content:
        content = None
    print("Message from " + user + ": " + str(content))

class PythonChat:
    def __init__(self,host,port,users):
        self.wasconnected = []
        self.users = users

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        self.sock.setblocking(1)

        self.sock.bind((host, port))
        self.sock.listen()
    def waitforfirstconn(self):
        while True:
            conn, addr = self.sock.accept()
            self.wasconnected.append(str(addr[0]))
            conn.send("Nano Server 0.1 OK".encode("utf-8"))

            currentuser = str(self.users.get(addr[0])[1])
            print("Connected from " + str(addr[0]) + " (" + currentuser + ")")

            anotherthread = threading.Thread(target=self.waitformsg,args=[conn,addr])
            anotherthread.daemon = True
            anotherthread.start()
    def waitformsg(self,conn1, addr1):
        try:
            msg = bytes(conn1.recv(4096)).decode("utf-8")
        except ConnectionResetError:
            print(str(addr1[0]) + " disconnected.")
        gotmsg(self.users.get(addr1[0])[1],msg)
    def connect(self,ip,port):
        self.sock.connect((ip,int(port)))
    def closesocket(self):
        self.sock.close()
    def getdata(self):
        conn, addr = self.sock.accept()
        data = conn.recv(4096)
        print(data)

print("Nano Chat Server " + __version__ + "\n------------------------")

with open("friends.txt","r") as file:
    file = file.readlines()
    users = {}
    for c, line in enumerate(file):
        if line.startswith("#"):
            continue

        thing = line.strip("\n").split("::")
        host1 = thing[0]
        port1 = thing[1]
        alias = thing[2]
        users[host1] = [port1, alias]

chat = PythonChat(hostd,portd,users)

chat.waitforfirstconn()