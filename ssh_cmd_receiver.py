import threading
from time import sleep
from ssh_tunnelmanager import TunnelManager
from ssh_common import port_manager
from ssh_common import permament_tunnel_manager

#CmdReceiver - służy do komunikacji z konkretnym db-shepherdem
class CmdReceiver(threading.Thread):
    def __init__(self, client,address):
        threading.Thread.__init__(self)
        self.t_manager = TunnelManager()
        self.client = client
        self.address = address
        self.size = 1024

#adres_user_password_sshport_remoteport
    def run(self):
        running = 1
        print("run_cli")
        try:
            while running:
                data = self.client.recv(self.size)
                if data:
                    cmd = data.decode("utf-8").split("_")
                    try:
                        adr = cmd[0]
                        usr = cmd[1]
                        passwd = cmd[2]
                        ssh = cmd[3]
                        remote = cmd[4]
                        permament = cmd[5]

                        tunnel = None
                        if permament == "no":
                            if self.t_manager.is_alive(adr):
                                tunnel = self.t_manager.get_tunnel(adr)
                            elif permament_tunnel_manager.is_alive(adr):
                                tunnel = permament_tunnel_manager.get_tunnel(adr)
                            else:
                                tunnel = self.t_manager.connect(adr, usr, passwd, int(remote), int(ssh)) #, keypath="")
                                for num in range(0,20):
                                    sleep(1)
                                    #print(tunnel.status)
                                    print("Waiting...")
                                    if tunnel.status == "ok":
                                        break
                                    if tunnel.status == "bad":
                                        break
                        elif permament == "yes":
                            if self.t_manager.is_alive(adr):
                                ret = "exist-non-permament"
                                self.client.send(ret.encode("utf-8"))
                                return
                            elif permament_tunnel_manager.is_alive(adr):
                                tunnel = permament_tunnel_manager.get_tunnel(adr)
                            else:
                                 tunnel = permament_tunnel_manager(adr, usr, passwd, int(remote), int(ssh)) #, keypath="")
                                for num in range(0,20):
                                    sleep(1)
                                    #print(tunnel.status)
                                    print("Waiting...")
                                    if tunnel.status == "ok":
                                        break
                                    if tunnel.status == "bad":
                                        break

                        ret =  tunnel.status + "_" + tunnel.host + "_" + str(tunnel.local)
                    except IndexError:
                        ret = "Za malo argumentow."
                    print("D: ",cmd)
                    print(ret)
                    self.client.send(ret.encode("utf-8"))

        except ConnectionResetError as e:
            for tunnel in self.t_manager.lista:
                tunnel._stop()
            print("Połączenie z clientem zostało przerwane");