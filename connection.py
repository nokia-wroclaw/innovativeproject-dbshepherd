import socket
import threading


class Connection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = 'localhost'
        self.port = 13931
        self.size = 1024
        self.state = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.lock = threading.Lock()

    def send(self, query=""):
        self.sock.send(query.encode('utf-8'))

    def get_state(self):
        self.lock.acquire()
        st = self.state
        self.state = None
        self.lock.release()
        return st

    def run(self):
        running = 1
        while running:
            data = self.sock.recv(self.size)
            if data:
                self.lock.acquire()
                self.state = data.decode("utf-8")
                self.lock.release()
