import threading
from time import sleep
from sshmodules.tunnelmanager import TunnelManager

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
                        tunnel_index = self.t_manager.connect(1234, cmd[0], "dbshepherd", "dbshepherd", int(cmd[1]),22) #, keypath="")
                        for num in range(0,15):
                            sleep(1)
                            #print(self.t_manager.lista[tunnel_index].status)
                            if self.t_manager.lista[tunnel_index].status == "ok":
                                break
                            if self.t_manager.lista[tunnel_index].status == "bad":
                                break
                        ret = self.t_manager.lista[tunnel_index].status     
                    except IndexError:
                        ret = "Za malo argumentow."

                    print(ret)
                    self.client.send(ret.encode("utf-8"))

        except ConnectionResetError as e:
            for tunnel in self.t_manager.lista:
                tunnel._stop()
            print("Połączenie z clientem zostało przerwane");