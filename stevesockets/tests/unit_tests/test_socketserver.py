import unittest
from stevesockets.socketserver import SocketServer
import threading
import time


class TestSocketServerSetup(unittest.TestCase):

    def setUp(self):
        self.server = SocketServer("localhost", port=9000)
        self.t = threading.Thread(target=self.server.serve)

    def test_socket_server_setup(self):
        self.assertFalse(self.server.alive)
        self.t.start()
        time.sleep(.5)
        self.assertTrue(self.server.alive)
        self.server.stop()
        self.t.join()


class TestSocketServerResponse(unittest.TestCase):

    def setUp(self):
        self.server = SocketServer("localhost", port=9000)
        self.t = threading.Thread(target=self.server.serve)

    def test_socket_server_response(self):
        self.server.on_message = lambda conn, d: int(d) + 1
        self.t.start()
