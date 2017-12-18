import socket
import select
import threading
import time
import re
import os
from datetime import datetime
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s-%(name)s-%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SocketServer(object):

    def __init__(self, address, port=9000, listen_max=5, on_message=None):
        self.address = address
        self.port = port
        self.listen_max = listen_max
        self.all_connections = []
        self.on_message = on_message or getattr(self, "on_message", None)
        self.alive = False
        self.connection_threads = []

    def serve(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.address, self.port))
        self.socket.listen(self.listen_max)
        self.alive = True

        try:
            while self.alive:
                if select.select([self.socket], [], [])[0]:
                    conn, addr = self.socket.accept()
                    logging.debug("New connection from '{addr}'".format(addr=addr[0]))
                    self.all_connections.append(conn)
                    t = threading.Thread(target=self.handle_connection, args=(conn, addr))
                    self.connection_threads.append(t)
                    t.start()
        finally:
            logging.debug("Stopping server")
            self.stop()
            self.socket.close()

    def handle_connection(self, conn, address):
        try:
            while self.alive:
                try:
                    data = conn.recv(1024)
                except socket.error as err:
                    break

                if not data:
                    break
                elif self.on_message:
                    self.on_message(conn, data)
        finally:
            logging.debug("Closing connection at '{addr}'".format(addr=address[0]))
            conn.close()
            self.all_connections = [c for c in self.all_connections if c != conn]

    def stop(self):
        self.alive = False
        logging.debug("Killing {x} connections".format(x=len(self.all_connections)))
        [c.close() for c in self.all_connections]
        logging.debug("Killing {x} threads".format(x=len(self.connection_threads)))
        [t.join() for t in self.connection_threads]


class HttpServer(SocketServer):
    METHODS = ("GET")
    REQ_REGEX = re.compile(r"(\w+) ([^\s]+) (\w+)/(\d+\.\d+)")

    def __init__(self, address, port=50007, listen_max=5, on_message=None, server_name="HttpServer", docroot="/var/www/steve"):
        super(HttpServer, self).__init__(address, port, listen_max, on_message)
        self.docroot = docroot
        self.server_name = server_name

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
                    "Server: {server_name}",
                    "Connection: close\n\n"]).format(status_code=status_code,
                                                     status=status,
                                                     date_str=date_str,
                                                     server_name=self.server_name)
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
            response = self._get_404_response()
        connection.sendall(response)
        connection.close()

    def _get_404_response(self):
        header = self._generate_headers(404)
        body = "<p>404 Page Not Found</p>"
        if hasattr(self, "_not_found_page") and self._not_found_page:
            with open(self._not_found_page, "r") as f:
                body = f.read()
        return header + body

    def set_404_page(self, path):
        self._not_found_page = path

if __name__ == "__main__":
    s = HttpServer("localhost", port=80)
    s.set_404_page(s.docroot + "/404.html")
    print("Serving @ '{addr}' on port {port}".format(addr="localhost", port=80))
    s.serve()
