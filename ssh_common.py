from ssh_tunnelmanager import TunnelManager
permament_tunnel_manager = TunnelManager()

class PortManager(object):
    global_port = 13931

    def get_port(self):
        self.global_port += 1
        return self.global_port

port_manager = PortManager()
