import paramiko

# test.copy_to('.\conf.yaml','./conf.yaml_test')
# test.copy_from('./conf.yaml_test','.\conf.yaml_back')

# TODO!
# !!!! Wyjątki !!!!
# laczenie sie z uzyciem klucza
# Tworzenie tunelu
# zastanowic sie nad set_missing_host_key_policy

class Ssh:
	def __init__(self):
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	
	def manual_connect(self):
		ip = input("IP: ")
		user =  input("User: ")
		passwd = input("Pass: ")
		self.passwd_connect(ip,user,passwd)

	def passwd_connect(self,ip,user,passwd):
		try:
			self.ssh.connect(ip, username=user, password=passwd,port=22) 
		except TimeoutError as e:
			print (e)
			exit()
		except ConnectionRefusedError as e:
			print (e)
			exit()
		except paramiko.ssh_exception.AuthenticationException as e:
			print (e)
			exit()
		self.trans = self.ssh.get_transport()

	def rsa_connect(self,ip,user,rsa):
		pass
		
	def copy_to(self,localpath,remotepath):
		# kopiowanie
		sftp = paramiko.SFTPClient.from_transport(self.trans)
		try:
			sftp.put(localpath, remotepath)
		except FileNotFoundError as e:
			print (e)
		sftp.close()
	
	def copy_from(self,remotepath,localpath):
		sftp = paramiko.SFTPClient.from_transport(self.trans)
		try:
			sftp.get(remotepath, localpath)
		except FileNotFoundError as e:
			print (e)
		sftp.close()
	
	def close(self):
		trans.close()
	
	def ssh_commandline(self,command):
		while 1:
			cmd = input("Enter something: ")
			print ("to send:", cmd)
			if (cmd == ""):
				exit()
			chan = self.trans.open_session()
			try:
				chan.exec_command(cmd)
				#sprawdzamy czy jeszcze czegoś nie musimy dosłać
				#while chan.send_ready():
				#	cmd = input("Enter: ")
				#	chan.send(cmd.encode()) # send potrzebuje byte, exec_command stringa
			except SSHException:
				print ("Channel is kaput :(")
				exit()

			stdout = chan.recv(9999)
			stderr = chan.recv_stderr(9999)
			if stdout.decode() != "":
				print ("std:", stdout.decode())
			if stderr.decode() != "":
				print (stderr.decode())