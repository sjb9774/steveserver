import unittest
from stevesockets.socketserver import SocketServer
import threading
import time

class TestSocketServerSetup(unittest.TestCase):

    def setUp(self):
        self.server = SocketServer("localhost", port=9000)
        self.t = threading.Thread(target=self.server.serve)
        self.t.start()
        time.sleep(.5)

    def test_socket_server_ping(self):
        self.assertTrue(self.server.alive)
        self.server.stop()
        self.t.join()
        self.assertFalse(self.server.alive)
