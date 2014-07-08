import select
import socket
import threading
import logging
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

		#String zawierajacy format logów"
		fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
		#Init loggera
		#logl = getattr(logging, loglevel.upper(), None)
		#if not isinstance(numeric_level, int):
		#	logl = logging.INFO
		logging.basicConfig(filename='ssh_shepherd.log',level=logging.DEBUG, format=fmt)

		#Jako że używamy filename. musimy dodać handler do stdout
		stream = logging.StreamHandler()
		formatter = logging.Formatter(fmt)
		stream.setFormatter(formatter)
		logging.getLogger().addHandler(stream)
		#Ochodzą nas nasze loggery tylko
		for handler in logging.root.handlers:
			handler.addFilter(logging.Filter('root'))
		
	def open_socket(self):
		try:
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.bind((self.host,self.port))
			self.server.listen(5)

		except socket.error as e:
			logger.error(e)

	def run(self):
		self.open_socket()
		
		self.permament_checker = PermTunnelChecker()
		self.permament_checker.start()

		running = 1
		
		while running:
			ready = select.select([self.server], [self.server], [self.server], 1)

			for s in ready[0]:
				if s == self.server:
					logging.debug("connection")	
					connection = self.server.accept()
					logging.debug("create")
					c = CmdReceiver(connection[0], connection[1])
					logging.debug("start")
					self.threads.append(c)
					c.start();
		self.server.close()
		self.permament_checker.running = false

		for c in self.threads:
			c.join()

class PermTunnelChecker(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		self.running = True
		while self.running:
			sleep(60)
			logging.info("checking permament tunnels...")
			for t in ssh_common.permament_tunnel_manager.lista:
				t.is_alive()
				if t.status == "bad":
					t.restart()