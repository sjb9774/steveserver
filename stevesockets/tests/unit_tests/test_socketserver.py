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
