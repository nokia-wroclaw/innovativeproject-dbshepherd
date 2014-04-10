import threading


class Client(threading.Thread):
    def __init__(self, client,address):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024

    def run(self):
        running = 1
        print("run_cli")
        while running:
            data = self.client.recv(self.size)
            if data:
                print(data.decode("utf-8"))