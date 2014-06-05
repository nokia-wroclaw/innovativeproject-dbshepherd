import select
import paramiko
import threading
from socket import error
try:
	import SocketServer
except ImportError:
	import socketserver as SocketServer

class TunnelException(Exception):
	def __init__(self, msg):
		self.msg = msg

class ForwardServer(SocketServer.ThreadingTCPServer):
	daemon_threads = True
	allow_reuse_address = True


class Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		try:
			chan = self.ssh_transport.open_channel(b'direct-tcpip',('localhost', self.chain_port),('localhost', self.chain_localport))
		except Exception as e:
			print(e)
			print('Incoming request to %s:%d failed: %s' % (self.chain_host,self.chain_port,repr(e)))
			return
		if chan is None:
			print('Incoming request to %s:%d was rejected by the SSH server.' % (self.chain_host, self.chain_port))
			return
		print('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(), chan.getpeername(), (self.chain_host, self.chain_port)))
		while True:
			r, w, x = select.select([self.request, chan], [], [])
			if self.request in r:
				data = self.request.recv(1024)
				if len(data) == 0:
					break
				chan.send(data)
			if chan in r:
				data = chan.recv(1024)
				if len(data) == 0:
					break
				self.request.send(data)

		peername = self.request.getpeername()
		chan.close()
		self.request.close()
		print('Tunnel closed from %r' % (peername,))


def forward_tunnel(local_port, remote_host, remote_port, transport):
	class SubHandler(Handler):
		chain_host = remote_host
		chain_port = remote_port
		chain_localport = local_port
		ssh_transport = transport

	tunnel = ForwardServer(('', local_port), SubHandler)
	return tunnel


class TunnelThread(threading.Thread):
	def __init__(self, local_port, remote_host, remote_port, client):
		threading.Thread.__init__(self)
		self.local_port = local_port
		self.remote_host = remote_host
		self.remote_port = remote_port
		self.client = client
		self.forward_server = None

	def run(self):
		self.forward_server = forward_tunnel(self.local_port, self.remote_host, self.remote_port,
											 self.client.get_transport())
		self.forward_server.serve_forever()

	def stop(self):
		self.forward_server.shutdown()


class Tunnel():
	def __init__(self, local_port, remote_host, remote_port, user_name, passwd):
		self.client = paramiko.SSHClient()
		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		
		self.th = None
		self.status = "unknown"
		self.remote_host = remote_host
		self.remote_port = remote_port
		self.local_port = local_port
		self.passwd = passwd
		self.user_name = user_name
		try:
			print("Connecting to", remote_host)
			self.client.connect(remote_host, username=user_name, password=passwd)
			self.th = TunnelThread(local_port, remote_host, remote_port, self.client)
			self.th.start()
			self.status = 'ok'
		except ConnectionRefusedError:
			self.status = "bad"
			raise TunnelException("ConnectionRefusedError")
		except paramiko.ssh_exception.AuthenticationException as e:
			self.status = "bad"
			raise TunnelException(e)
		except paramiko.ssh_exception.SSHException as e:
			self.status = "bad"
			raise TunnelException(e)
		except error as e:
			self.status = "bad"
			raise TunnelException("SocketError: " +str(e.errno))
		except Exception as e:
			self.status = "bad"
			raise TunnelException(e)
		except:
			#other unhandled exceptions
			self.status = "unknown"
			raise TunnelException("Unknown Exception")

	def is_alive(self):
		try:
			chan = self.client.get_transport().open_session()
			chan.exec_command("uname")
		except Exception as e:
			self.status = "bad"

	def restart(self):
		self.stop()
		self.__init__(self.local_port, self.remote_host, self.remote_port, self.user_name, self.passwd)

	def stop(self):
		if self.th != None:
			self.th.stop()

# t = Tunnel(1234, 'antivps.pl', 5432, 'dbshepherd', 'dbshepherd')
# import time
# time.sleep(20)
# t.restart()
# print("Test")
# time.sleep(60)
# print("stop")
# t.stop()

# t2 = Tunnel('localhost', 1235, 'kax-gate.noip.me', 443, 'nsn', 'nsnshepherd')

    