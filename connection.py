import socket
import threading


class Connection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = 'localhost'
        self.port = 13931
        self.size = 1024
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send(self, query=""):
        line = "server1_base1_1234_5432"
        self.sock.send(query.encode('utf-8'))

    def run(self):
        running = 1
        while running:
            pass
            # line = "server1_base1_1234_5432"
