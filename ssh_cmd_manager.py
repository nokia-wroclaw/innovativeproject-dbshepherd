import select
import socket
import threading
from ssh_cmd_receiver import CmdReceiver
import ssh_tunnelmanager
import ssh_common
from time import sleep
ssh_common.permament_tunnel_manager = ssh_tunnelmanager.TunnelManager()

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
		
		permament_checker = PermTunnelChecker()
		permament_checker.start()
		
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
		permament_checker.running = false
		permament_checker.join()
		for c in self.threads:
			c.join()
class PermTunnelChecker(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
	self.running = True
		while self.running:
			print("test")
			for t in ssh_common.permament_tunnel_manager.lista:
				t.is_alive()
				if t.status == "bad":
					print("wznawiam")
			sleep(60)