import paramiko
import time
import sys

import threading
import configmanager
from socket import error
import errno
from ssh_tunnel import forward_tunnel
import ssh_common

class TunnelManagerException(Exception):
    def __init__(self, msg):
        self.msg = msg


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
		self.status = "unknown"
	def run(self):
		try:
			self.forward(self.local, self.host, self.user, self.passwd, self.remote, self.ssh_port, self.keypath)
		except TunnelManagerException as e:
			print ("Unable to create tunnel (", self.host, ") reason:", e)
			self.status = "bad"
	def forward(self, local_port, host, user, passwd, remote_port, ssh, key):
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
			#tutaj juz powinnismy byc podlaczeni
			self.status="ok"
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

class TunnelManager(object):
	def __init__(self):
		self.lista =[]
	def connect(self, host, user, passwd, remote_port, ssh_port, keypath=""):
		try:
			index = len(self.lista)
			## BLOKOWANIE ##
			local_port = ssh_common.port_manager.get_port()
			################
			w = Tunnel(local_port, host, user, passwd, remote_port, ssh_port, keypath)

			self.lista.append(w)
			w.start()
			return self.lista[index]
		except TunnelManagerException as e:
			raise TunnelManagerException(e)
	def connectToAlias(self, args):
		yaml = configmanager.ConfigManager("conf.yaml")
		connection = yaml.get(args.split()[0])['connection']
		try:
			passwd = connection['passwd']
		except KeyError:
			passwd = input("Password: ")
		try:
			self.connect(connection['localport'],connection['adress'],connection['user'],"",connection['remoteport'],connection['sshport'],args.split()[1])
		except IndexError:
			self.connect(connection['localport'],connection['adress'],connection['user'],passwd,connection['remoteport'],connection['sshport'])
	
	def is_alive(self, host_name,remote):
		for tunnel in self.lista:
			if tunnel.host == host_name and tunnel.remote == int(remote) and tunnel.status == 'ok':
				return True
		return False
		
	def get_tunnel(self, host_name,remote):
		for tunnel in self.lista:
			if tunnel.host == host_name and tunnel.remote == int(remote) and tunnel.status == 'ok':
				return tunnel
		return None
	
	def clean(self):
		
		print("clean")
		print(len(self.lista))
		for tunnel in self.lista :
			if(tunnel.status == "bad" or tunnel.status == "unknown" ):
				print ("trying to del", tunnel.name)
				#blokowanie? 
				del self.lista[self.lista.index(tunnel)]
		print(len(self.lista))