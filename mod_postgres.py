from prettytable import from_db_cursor
from mod_core import ModuleCore, ParseArgsException
import common
from configmanager import ConfigManager, ConfigManagerError
import psycopg2
import os
import paramiko
import datetime
from subprocess import Popen, PIPE

import sys
import io
import select

class Postgres(ModuleCore):
	def __init__(self, completekey='tab', stdin=None, stdout=None):
		super().__init__()
		self.set_name('Postgres')
		self.warn = False

	def psycop_query(self, db_name, db_user, db_passwd, db_host, db_port, db_query):
		try:
			pg_conn = psycopg2.connect(dbname=db_name, user=db_user, host=db_host, password=db_passwd, port=db_port)
			pg_conn.autocommit = True;
			cur = pg_conn.cursor()
			cur.execute(db_query)

			pt = from_db_cursor(cur)
			if pt != None:
				print(pt)

		except psycopg2.Error as e:
			print('--------------------')
			print('Error:', e, end='')
			print('--------------------')
		except psycopg2.Warning as w:
			print('--------------------')
			print('Warning:', w, end='')
			print('--------------------')
		except psycopg2.InterfaceError as e:
			print('--------------------')
			print('Error:', e, end='')
			print('--------------------')
		except psycopg2.DatabaseError as e:
			print('--------------------')
			print('Error:', e, end='')
			print('--------------------')

	def exe_query(self, file_name, serv_name, base_name, db_query):
		cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
		conn = cnf["connection"]
		database = cnf["databases"][base_name]

		if conn["type"] == "ssh":
			cmd = conn["adress"] + "_" + conn["user"] + "_" + conn["passwd"] + "_" + str(conn["sshport"]) + "_" + str(conn["remoteport"]) + "_no"
			common.conn.send(cmd)
			ans = None
			while ans == None:
				ans = common.conn.get_state()

			status, hostname, db_port = ans.split("_")
			adr = "localhost"

			if status == "ok":  #udało się utworzyć tunel
				self.psycop_query(database["name"], database["user"], database["passwd"], adr, db_port, db_query)
			else:
				print('--------------------')
				print('Error: Unable to create ssh tunnel')
				print('--------------------')

		elif conn["type"] == "direct":
			self.psycop_query(database["name"], database["user"], database["passwd"], conn["adress"], conn["remoteport"], db_query)

	def do_query(self, args):
		try:
			(values, num) = self.parse_args(args, 1, 2)

			if num == 2:
				self.exec_on_config(self.exe_query, [values[1]], values[0],'list')
			elif num == 1:
				self.exec_on_config(self.exe_query, [values[0]], '', 'list')

		except ConfigManagerError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except ParseArgsException as e:
			print(e)
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')

	# ------------------------------------------------------------------------------------------------------------------

	def local_dump(self, db_name, db_user, db_pass, host, port, file_name, type = 'sql'):
		dumper = """pg_dump.exe -U %s -d %s -h %s -p %s -f %s -C --column-inserts"""

		if type == 'tar':
			dumper += ' -Ft'
			dump_file_name = file_name + '.tar'
		else:
			dump_file_name = file_name + '.sql'

		command = dumper % (db_user, db_name, host, port, dump_file_name)

		os.putenv('PGPASSWORD', db_pass)
		try:
			proc = Popen(command, stdout=PIPE, stderr=PIPE)
		except FileNotFoundError:
			raise PostgressError(" ERROR: pg_dump not found")

		stderr = b'';
		for line in proc.stderr:
			stderr += line

		if stderr != b'':
			raise PostgressError(stderr.decode('iso_8859_2', 'ignore'))

	def remote_dump(self, db_name, db_user, db_pass, con_user, con_pass, host, sshport, remoteport, file_name, type = 'sql'):
		dumper = "pg_dump -U %s -d %s -C --column-inserts"

		if type == 'tar':
			dumper += ' -Ft'
			dump_file_name = file_name + '.tar'
		else:
			dump_file_name = file_name + '.sql'

		os.putenv('PGPASSWORD', db_pass)
		command = dumper % (db_user, db_name)
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(host, username=con_user ,password=con_pass, port=sshport)
		channel = client.get_transport().open_session()
		channel.exec_command(command)

		stderr = b''
		cmd = channel.recv_stderr(256)
		while cmd != b'':
			stderr += cmd
			cmd = channel.recv_stderr(256)

		if stderr == b'':
			stdout = b''
			cmd = channel.recv(256)
			while cmd != b'':
				stdout += cmd
				cmd = channel.recv(256)

			file = open(dump_file_name, 'wb')
			file.write(stdout)
			file.close()
		else: # nie udało się pg_dumpem z serwera, próba pg_dumpem lokalnym
			if self.warn == True:
				print('--------------------')
				print('WARNING: '+stderr.decode('iso_8859_2', 'ignore')+'attempt to use the local pg_dump')
			cmd = host + "_" + con_user + "_" + con_pass + "_" + str(sshport) + "_" + str(remoteport) + "_no"
			common.conn.send(cmd)
			ans = None
			while ans == None:
				ans = common.conn.get_state()

			if ans.split('_')[0] == 'ok':
				# self.local_dump(db_name, db_user, db_pass, '127.0.0.1', int(ans.split("_")[2]), dump_file_name, type)
				self.local_dump(db_name, db_user, db_pass, '127.0.0.1', int(ans.split("_")[2]), file_name, type)
				if self.warn == True:
					print('SUCCESS')
					print('--------------------')
			else:
				if self.warn != True:
					print('--------------------')
				print('FAIL')
				print('--------------------')

	def exe_dump(self, file_name, serv_name, base_name, backup_name, type):
		try:
			date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
			cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
			conn = cnf["connection"]
			db = cnf["databases"][base_name]
			dump_file_name = 'dump/'+backup_name+'_'+file_name+'_'+serv_name+'_'+base_name+'_'+date

			if conn["type"] == "ssh": #Dla połączeń ssh
				self.remote_dump(db["name"], db["user"], db["passwd"], conn["user"], conn["passwd"], conn["adress"], conn["sshport"], conn["remoteport"], dump_file_name, type)
			elif conn["type"] == "direct":
				self.local_dump(db["name"], db["user"], db["passwd"], conn["adress"], conn["remoteport"], dump_file_name, type)
		except ConnectionRefusedError:
			print('--------------------')
			print('ERROR: Connection Refused by host')
			print('--------------------')
			return False

		except TimeoutError:
			print('--------------------')
			print('ERROR: Connection timeout')
			print('--------------------')
			return False

		except paramiko.ssh_exception.AuthenticationException:
			print('--------------------')
			print('ERROR: Authentication problem')
			print('--------------------')
			return False

		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
			return False

		except PostgressError as e:
			print('--------------------')
			print('ERROR:',e, end='')
			print('--------------------')
			return False

		except Exception as e:
			print(type(e))
			print(e)
			return False

	def do_dump(self, args):
		try:
			(values, num) = self.parse_args(args, 1, 2)

			if num == 2:
				self.exec_on_config(self.exe_dump, [values[1], 'sql'], values[0], 'tree')
			elif num == 1:
				self.exec_on_config(self.exe_dump, [values[0], 'sql'], '', 'tree')

		except ConfigManagerError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except ParseArgsException as e:
			print(e)
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')

	def do_dump_tar(self, args):
		try:
			(values, num) = self.parse_args(args, 1, 2)

			if num == 2:
				self.exec_on_config(self.exe_dump, [values[1], 'tar'], values[0], 'tree')
			elif num == 1:
				self.exec_on_config(self.exe_dump, [values[0], 'tar'], '', 'tree')

		except ConfigManagerError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except ParseArgsException as e:
			print(e)
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
# ----------------------------------------------------------------------------------------------------------------------

	def local_restore(self, db_name, db_user, db_pass, host, port, file_name, type = 'sql'):
		if type == 'tar': #jeżeli restorujemy tar'a
			restorer = "pg_restore -U %s -d %s -h %s -p %s"
			command = restorer % (db_user, db_name, host, port)
			os.putenv('PGPASSWORD', db_pass)

			bytes_read = open(file_name, "rb")

			try:
				proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=bytes_read)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_restore not found")

			stderr = b'';
			for line in proc.stderr:
				stderr += line

			if stderr != b'':
				raise PostgressError(stderr.decode('utf8', 'ignore'))
		else:
			restorer = "psql -U %s -d %s -h %s -p %s"
			command = restorer % (db_user, db_name, host, port)
			os.putenv('PGPASSWORD', db_pass)

			bytes_read = open(file_name, "rb")

			try:
				proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=bytes_read)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_restore not found")

			stderr = b'';
			for line in proc.stderr:
				stderr += line

			if stderr != b'':
				raise PostgressError(stderr.decode('utf8', 'ignore'))

	def remote_restore(self, db_name, db_user, db_pass, con_user, con_pass, host, sshport, remoteport, file_name, type = 'sql'):
		restorer = "pg_restore -U %s -d %s -h %s -p %s"


		# os.putenv('PGPASSWORD', db_pass)
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(host, username=con_user ,password=con_pass, port=sshport)
		channel = client.get_transport().open_session()
		channel.exec_command("pg_dump -W")
		channel.send('pass\n'.encode())
		channel.send('pass\n'.encode())


		stderr = b''
		cmd = channel.recv_stderr(1)
		while cmd != b'':
			stderr += cmd
			cmd = channel.recv_stderr(1)

		if stderr == b'':
			stdout = b''
			cmd = channel.recv(1)
			while cmd != b'':
				stdout += cmd
				cmd = channel.recv(1)

		print(stderr.decode('utf-8', 'ignore'), stdout.decode('utf-8', 'ignore'))




	def do_restore(self, args):
		try:
			# self.local_restore('postgres', 'postgres', 'root', '127.0.0.1', 5432, 'local.sql', type = 'sql')
			self.remote_restore('postgres', 'postgres', 'root', 'seba', 'seba', '127.0.0.1', 23, 5432, 'proba.tar', 'tar')
		except PostgressError as e:
			print(e)


class PostgressError(Exception):
	def __init__(self, value):
		self.value = value