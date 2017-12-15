import socket
import thread
import time
import re
import os
from datetime import datetime

class SocketServer(object):

    def __init__(self, address, port=50007, listen_max=5, on_message=None):
        self.address = address
        self.port = port
        self.listen_max = listen_max
        self.all_connections = []
        self.on_message = on_message or getattr(self, "on_message")

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
        try:
            while 1:
                try:
                    data = conn.recv(1024)
                except socket.error as err:
                    break

                if not data:
                    break
                elif self.on_message:
                    self.on_message(conn, data)
        finally:
            conn.close()
            self.all_connections = [c for c in self.all_connections if c != conn]


class HttpServer(SocketServer):
    METHODS = ("GET")
    REQ_REGEX = re.compile(r"(\w+) ([^\s]+) (\w+)/(\d+\.\d+)")

    def __init__(self, address, port=50007, listen_max=5, on_message=None, docroot="/var/www/steve"):
        super(HttpServer, self).__init__(address, port, listen_max, on_message)
        self.docroot = docroot

    def on_message(self, conn, data):
        matches = self.REQ_REGEX.findall(data)
        method, path, protocol, version = matches[0]

        if method in self.METHODS:
            getattr(self, "_handle_{method}_req".format(method=method.lower()))(connection=conn,
                                                                                method=method,
                                                                                path=path,
                                                                                protocol=protocol,
                                                                                version=version,
                                                                                data=data)

    def _get_status(self, code):
        codes = {
            200: "OK",
            404: "Not Found"
        }
        return codes.get(code)

    def _generate_headers(self, status_code):
        date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
        status = self._get_status(status_code)
        header = "\n".join(["HTTP/1.1 {status_code} {status}",
                    "Date: {date_str}",
                    "Server: Steve-HTTP-Server",
                    "Connection: close\n\n"]).format(status_code=status_code, status=status, date_str=date_str)
        return header

    def _handle_get_req(self,
                        connection=None,
                        method=None,
                        path=None,
                        protocol=None,
                        version=None,
                        data=None):

        requested_path = "{docroot}{path}".format(docroot=self.docroot, path=path)
        response = ""
        if os.path.exists(requested_path) and not os.path.isdir(requested_path):
            header = self._generate_headers(200)
            with open(requested_path, "r") as f:
                body = f.read()
            response = header + body
        else:
            header = self._generate_headers(404)
            body = "<p>404 Page Not Found</p>"
            response = header + body
        connection.sendall(response)
        connection.close()

if __name__ == "__main__":
    s = HttpServer("localhost", port=80)
    s.serve()
