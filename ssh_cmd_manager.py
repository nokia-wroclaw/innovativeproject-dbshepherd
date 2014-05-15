import select
import socket
import threading
from ssh_cmd_receiver import CmdReceiver


#CmdManager (Server połączeń)
#Odbiera połączenia od db-shepherd'ów
#tworzy im własnych odbiorców poleceń (CmdReceiver)
class CmdManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = ''
        self.port = 13931
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host,self.port))
            self.server.listen(5)

        except socket.error as e:
            print(e)

    def run(self):
        self.open_socket()

        running = 1
        while running:
            ready = select.select([self.server], [self.server], [self.server], 1)

            for s in ready[0]:
                if s == self.server:
                    print("connection")
                    connection = self.server.accept()
                    print("create")
                    c = CmdReceiver(connection[0], connection[1])
                    print("start")
                    c.start();
        self.server.close()
        for c in self.threads:
            c.join()


s = CmdManager();
s.start();

