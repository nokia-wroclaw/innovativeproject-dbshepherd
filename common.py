import connection
conn = None

from ssh_tunnelmanager import TunnelManager
permament_tunnel_manager = TunnelManager()

try:
    conn = connection.Connection()
    conn.start()
    print("test")
except ConnectionRefusedError:
    print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")