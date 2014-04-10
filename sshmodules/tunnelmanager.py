import paramiko
import time
import sys

sys.path.append("..")

import threading
import configmanager
from socket import error  #sock 10060
import errno
from sshmodules.tunnel import forward_tunnel


class TunnelManagerException(Exception):
	def __init__(self, msg):
		self.msg = msg

def forward(local_port, host, user, passwd, remote_port, ssh, key):
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	try:
		print ('connecting to', host)
		if(key==""):
			client.connect(host,username=user, password=passwd,port=ssh)
		else:
			try:
				mykey = paramiko.RSAKey.from_private_key_file(key,"qwerty12")
			except paramiko.PasswordRequiredException:
				raise TunnelManagerException("Encrypted key, no password")
			client.connect(host,username=user, port=ssh, pkey=mykey)
		print ('connected')
		try:
			forward_tunnel(local_port, '127.0.0.1', remote_port, client.get_transport())
		except SystemExit:
			raise TunnelManagerException("C-c: Port forwarding stopped.")
	except ConnectionRefusedError:
		raise TunnelManagerException("ConnectionRefusedError")
	except paramiko.ssh_exception.AuthenticationException as e:
	 	raise TunnelManagerException(e)
	except paramiko.ssh_exception.SSHException as e:
		raise TunnelManagerException(e)
	except error as e: #sock 10060 timeout, 10013 socket juz zajety
		raise TunnelManagerException(e.errno)
	except Exception as e:
		raise TunnelManagerException(e)
	except:
		# other unhandled exceptions
		raise TunnelManagerException("Unknown Exception")

class Tunnel(threading.Thread):
	def __init__(self, local_port, host, user, passwd, remote_port,ssh_port,keypath):
		threading.Thread.__init__(self)
		self.name = host
		self.host = host
		self.user = user
		self.passwd = passwd
		self.local = local_port
		self.remote = remote_port
		self.ssh_port = ssh_port
		self.keypath = keypath
		self.status = "ok"
	def run(self):
		try:
			forward(self.local, self.host, self.user, self.passwd, self.remote, self.ssh_port, self.keypath)
		except TunnelManagerException as e:
			print ("Unable to create tunnel (", self.host, ") reason:", e)
			self.status = "bad"

class TunnelManager():
	def __init__(self):
		self.lista =[]

	def connect(self,local_port, host, user, passwd, remote_port, ssh_port, keypath=""):
		try:
			w = Tunnel(local_port, host, user, passwd, remote_port, ssh_port, keypath)
			self.lista.append(w)
			w.start()
		except TunnelManagerException as e:
			raise TunnelManagerException(e)
	def connectToAlias(self, args):
		yaml = configmanager.ConfigManager("conf.yaml")
		connection = yaml.show(args.split()[0])['connection']
		try:
			passwd = connection['passwd']
		except KeyError:
			passwd = input("Password: ")
		try:
			self.connect(connection['localport'],connection['adress'],connection['user'],"",connection['remoteport'],connection['sshport'],args.split()[1])
		except IndexError:
			self.connect(connection['localport'],connection['adress'],connection['user'],passwd,connection['remoteport'],connection['sshport'])

	def clean(self):
		for tunnel in self.lista:
			#print (tunnel)
			if(tunnel.status == "bad"):
				print ("trying to del", tunnel.name)
				del self.lista[self.lista.index(tunnel)]