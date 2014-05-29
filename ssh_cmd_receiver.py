import threading
from time import sleep
import ssh_tunnelmanager
import ssh_common

#CmdReceiver - służy do komunikacji z konkretnym db-shepherdem
class CmdReceiver(threading.Thread):
    def __init__(self, client,address):
        threading.Thread.__init__(self)
        self.t_manager = ssh_tunnelmanager.TunnelManager()
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
                    ret = "Unknown Error"

                    cmd = data.decode("utf-8").split("_")
                    if len(cmd) == 1:
                        # cmd;arg1;arg2;arg3 ...
                        cmd = cmd[0].split(";")
                        if cmd[0] == "clean" and len(cmd) > 1:
                            #Clean tunnels
                            tunnels_to_clean = cmd[1:]
                            for tunnel in tunnels_to_clean:
                                #See if it is active? Kill it anyway?
                                for t in self.t_manager.lista:
                                    if tunnel == t.host: #
                                        t._stop()
                                        del self.t_manager.lista[self.t_manager.lista.index(t)]
                                        ret = "Disconnected"
                                for t in ssh_common.permament_tunnel_manager.lista:
                                    if tunnel == t.host: #
                                        t._stop()
                                        del ssh_common.permament_tunnel_manager.lista[ssh_common.permament_tunnel_manager.lista.index(t)]
                                        ret = "Disconnected"
                    else:
                        try:
                            adr = cmd[0]
                            usr = cmd[1]
                            passwd = cmd[2]
                            ssh = cmd[3]
                            remote = cmd[4]
                            permament = cmd[5]

                            tunnel = None
                            if permament == "no":
                                if self.t_manager.is_alive(adr,remote):
                                    tunnel = self.t_manager.get_tunnel(adr,remote)
                                elif ssh_common.permament_tunnel_manager.is_alive(adr,remote):
                                    tunnel = ssh_common.permament_tunnel_manager.get_tunnel(adr,remote)
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
                                if self.t_manager.is_alive(adr,remote):
                                    ret = "exist-non-permament"
                                    self.client.send(ret.encode("utf-8"))
                                    return
                                elif ssh_common.permament_tunnel_manager.is_alive(adr,remote):
                                    tunnel = ssh_common.permament_tunnel_manager.get_tunnel(adr,remote)
                                else:
                                    tunnel = ssh_common.permament_tunnel_manager(adr, usr, passwd, int(remote), int(ssh)) #, keypath="")
                                    for num in range(0,5):
                                        sleep(1)
                                        #print(tunnel.status)
                                        print("Waiting...")
                                        if tunnel.status == "ok":
                                            break
                                        if tunnel.status == "bad":
                                            # tu mozna wywołać "garbage collectora" do tuneli
                                            break

                            ret =  tunnel.status + "_" + tunnel.host + "_" + str(tunnel.local)
                        except IndexError:
                            ret = "Za malo argumentow."
                    print("D: ",cmd)
                    print(ret)
                    self.client.send(ret.encode("utf-8"))
                    #Chwilowo clean po kazdorazowym dodaniu tunelu
                    self.t_manager.clean()

        except ConnectionResetError as e:
            for tunnel in self.t_manager.lista:
                tunnel._stop()
            print("Połączenie z clientem zostało przerwane");