import socket
import thread
import time
import re

class SocketServer(object):

    def __init__(self, address, port=50007, listen_max=5, on_message=None, greeting="Connected"):
        self.address = address
        self.port = port
        self.listen_max = listen_max
        self.all_connections = []
        self.on_message = on_message or getattr(self, "on_message")
        self.greeting = greeting

    def serve(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.address, self.port))
        self.socket.listen(self.listen_max)

        try:
            while 1:
                conn, addr = self.socket.accept()
                self.all_connections.append(conn)
                thread.start_new_thread(self.handle_connection, (conn, addr))
        finally:
            self.socket.close()

    def handle_connection(self, conn, address):
        conn.sendall("{msg}\n".format(msg=self.greeting))
        try:
            while 1:
                data = conn.recv(1024)
                if not data:
                    break
                elif self.on_message:
                    self.on_message(conn, data)
        finally:
            conn.close()
            self.all_connections = [c for c in self.all_connections if c != conn]

def msg(server, connection, data):
    for c in server.all_connections:
        if connection != c:
            c.sendall("Data recieved from elsewhere: {msg}".format(msg=data))

def http(server, connection, data):
    print data

class HttpServer(SocketServer):

    REQ_REGEX = re.compile(r"(\w+) ([^\s]+) (\w+)/(\d+\.\d+)")

    def on_message(self, conn, data):
        matches = self.REQ_REGEX.findall(data)
        method, path, protocol, version = matches[0]
        print method, path, protocol, version

if __name__ == "__main__":
    s = HttpServer("localhost")
    s.serve()
