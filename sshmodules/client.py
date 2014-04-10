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
        try:
            while running:
                data = self.client.recv(self.size)
                if data:
                    print("D: ",data.decode("utf-8"))
                    str = "może sie udalo"
                    print(str)
                    self.client.send(str.encode("utf-8"))
        except ConnectionResetError as e:
            print("Połączenie z clientem zostało przerwane");