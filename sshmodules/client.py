import threading
from tunnelmanager import TunnelManager

class Client(threading.Thread):
    def __init__(self, client,address):
        threading.Thread.__init__(self)
        self.t_manager = TunnelManager()
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
                    cmd = data.decode("utf-8").split("_")
                    ret = "może sie udalo"
                    print("D: ",cmd)
                    try:
                        self.t_manager.connect(1234, cmd[0], "dbshepherd", "dbshepherd", int(cmd[1]),22) #, keypath="")
                    except IndexError:
                        ret = "Za malo argumentow."

                    
                    print(ret)
                    self.client.send(ret.encode("utf-8"))

        except ConnectionResetError as e:
            print("Połączenie z clientem zostało przerwane");