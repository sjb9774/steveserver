import unittest
from socket.stevesockets import socketserver
from thread import create_new_thread

class TestSocketServer(unittest.TestCase):

    def setUp(self):
        self.server = SocketServer("localhost")


    def test_socket_server_ping(self):
        pass
