import paramiko
import time
import sys
import threading
import configmanager
from forward import forward_tunnel


class TunnelManagerException(Exception):
	def __init__(self, msg):
		self.msg = msg



def forward(local_port, host, user, passwd, remote_port, ssh):
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	try:
		print ('connecting to', host)
		client.connect(host,username=user, password=passwd,port=ssh)
		print ('connected')
		try:
			forward_tunnel(local_port, '127.0.0.1', remote_port, client.get_transport())
		except SystemExit:
			raise TunnelManagerException("C-c: Port forwarding stopped.")
	except ConnectionRefusedError:
		raise TunnelManagerException("ConnectionRefusedError")
	except paramiko.ssh_exception.AuthenticationException as e:
		raise TunnelManagerException(e)
	except Exception as e:
		raise TunnelManagerException(e)
	except:
		# other unhandled exceptions
		raise TunnelManagerException("Unknown Exception")

class Tunnel(threading.Thread):
	def __init__(self, local_port, host, user, passwd, remote_port,ssh_port):
		threading.Thread.__init__(self)
		self.name = host
		self.host = host
		self.user = user
		self.passwd = passwd
		self.local = local_port
		self.remote = remote_port
		self.ssh_port = ssh_port
		self.status = "ok"
	def run(self):
		try:
			forward(self.local, self.host, self.user, self.passwd, self.remote, self.ssh_port)
		except TunnelManagerException as e:
			print (e)
			self.status = "bad"

class TunnelManager():
	def __init__(self):
		self.lista =[]
	def connect(self,local_port, host, user, passwd, remote_port, ssh_port):
		try:
			w = Tunnel(local_port, host, user, passwd, remote_port, ssh_port)
			self.lista.append(w)
			w.start()
		except TunnelManagerException as e:
			raise TunnelManagerException(e)
	def connectToAlias(self, server_alias):
		yaml = configmanager.ConfigManager("conf.yaml")
		connection = yaml.show(server_alias)['connection']
		try:
			passwd = connection['passwd']
		except KeyError:
			passwd = input("Password: ")
		self.connect(connection['localport'],connection['adress'],connection['user'],passwd,connection['remoteport'],connection['sshport'])

	def clean(self):
		for tunnel in self.lista:
			#print (tunnel)
			if(tunnel.status == "bad"):
				print ("trying to del", tunnel.name)
				del self.lista[self.lista.index(tunnel)]

# #ThreadMan.connect(1234,'antivps.pl','dbshepherd','dbshepherd',443,22)
