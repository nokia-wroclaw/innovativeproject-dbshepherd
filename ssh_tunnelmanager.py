import paramiko
import time
import sys

import threading
import configmanager
from socket import error
import errno
from ssh_tunnel import Tunnel, TunnelException
import ssh_common


class TunnelManagerException(Exception):
	def __init__(self, msg):
		self.msg = msg

class TunnelManager(object):
	def __init__(self):
		self.lista = []

	def connect(self, host, user, passwd, remote_port, ssh_port, keypath=""):
		try:
			index = len(self.lista)
			## BLOKOWANIE ##
			local_port = ssh_common.port_manager.get_port()
			################
			# w = Tunnel(local_port, host, user, passwd, remote_port, ssh_port, keypath)
			try:
				w = Tunnel(local_port, host, remote_port, user, passwd, ssh_port)
				self.lista.append(w)
				return self.lista[index]
			except TunnelException as e:
				print(e)
				return None
		except TunnelManagerException as e:
			raise TunnelManagerException(e)

	def is_alive(self, host_name, remote_port):
		for tunnel in self.lista:
			if tunnel.remote_host == host_name and tunnel.remote_port == int(remote_port) and tunnel.status == 'ok':
				return True
		return False

	def get_tunnel(self, host_name, remote_port):
		for tunnel in self.lista:
			if tunnel.remote_host == host_name and tunnel.remote_port == int(remote_port) and tunnel.status == 'ok':
				return tunnel
		return None

	def clean(self):
		print("clean")
		print(len(self.lista))
		for tunnel in self.lista:
			if (tunnel.status == "bad" or tunnel.status == "unknown" ):
				#blokowanie?
				tunnel.stop()
				del self.lista[self.lista.index(tunnel)]
		print(len(self.lista))