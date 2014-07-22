import os
import re
import common
import tarfile
import psycopg2
import paramiko
import datetime
from kp import KeePassError
from subprocess import Popen, PIPE
from prettytable import from_db_cursor
from mod_core import ModuleCore, ParseArgsException
from configmanager import ConfigManager, ConfigManagerError

class Postgres(ModuleCore):
	def __init__(self):
		super().__init__(module='Postgres')
		# self.set_name('Postgres')
		self.warn = False
		# self.do_cd('.')

	def get_local_version(self, cmd):
		proc = Popen(cmd , stdout=PIPE, stderr=PIPE, shell=True)
		out, err = proc.communicate()
		if err != b'':
			print('ERROR:', err.decode('utf8', 'ignore'))
		else:
			return re.findall(r'\d+.\d+.\d+', out.decode('utf8', 'ignore'))[0].split('.')

	def get_pg_version(self, db_name, db_user, db_passwd, db_host, db_port):
		try:
			pg_conn = psycopg2.connect(dbname=db_name, user=db_user, host=db_host, password=db_passwd, port=db_port)
			cur = pg_conn.cursor()
			cur.execute('select version()')
			return re.findall(r'\d+.\d+.\d+', cur.fetchone()[0])[0].split('.')
		except psycopg2.Error as e:
			print('--------------------')
			print('Error:', e)
			print('--------------------')
		except psycopg2.Warning as w:
			print('--------------------')
			print('Warning:', w)
			print('--------------------')
		except psycopg2.InterfaceError as e:
			print('--------------------')
			print('Error:', e)
			print('--------------------')
		except psycopg2.DatabaseError as e:
			print('--------------------')
			print('Error:', e)
			print('--------------------')

	def is_valid_versions(self, ver1, ver2):
		if ver1[0] > ver2[0]:
			return True
		elif ver1[0] == ver2[0]:
			if ver1[1] >= ver2[1]:
				return True
			else:
				return False
		else:
			return False

	def do_pg_versions(self, arg):
		"Print versions of your postgres tools"
		out = self.get_local_version('psql --version')
		if out != None:
			print('Local psql version:', out[0]+'.'+out[1]+'.'+out[2])

		out = self.get_local_version('pg_dump --version')
		if out != None:
			print('Local pg_dump version:', out[0]+'.'+out[1]+'.'+out[2])

		out = self.get_local_version('pg_restore --version')
		if out != None:
			print('Local pg_restore version:', out[0]+'.'+out[1]+'.'+out[2])

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
			print('Error:', e)
			print('--------------------')
		except psycopg2.Warning as w:
			print('--------------------')
			print('Warning:', w)
			print('--------------------')
		except psycopg2.InterfaceError as e:
			print('--------------------')
			print('Error:', e)
			print('--------------------')
		except psycopg2.DatabaseError as e:
			print('--------------------')
			print('Error:', e)
			print('--------------------')

	def exe_query(self, file_name, serv_name, base_name, db_query):
		conf = ConfigManager("config/" + file_name + ".yaml")
		cnf = conf.get(serv_name)
		conn = cnf["connection"]
		database = cnf["databases"][base_name]

		if conn["type"] == "ssh":
			cmd = self.connect_command_builder(conn, 'no')
			common.conn.send(cmd)
			ans = None
			while ans == None:
				ans = common.conn.get_state()

			status, hostname, db_port = ans.split("_")
			adr = "localhost"

			if status == "ok":  #udało się utworzyć tunel
				self.psycop_query(database["name"], database["user"], conf.get_password(serv_name + '.' + base_name), adr, db_port, db_query)
			else:
				print('--------------------')
				print('Error: Unable to create ssh tunnel')
				print('--------------------')

		elif conn["type"] == "direct":
			self.psycop_query(database["name"], database["user"], conf.get_password(serv_name + '.' + base_name), conn["adress"], conn["remoteport"], db_query)

	def do_query(self, args):
		'Do query to database\n\tUsage:\tquery "query"\t\t (query using all server lists)\n\t\tquery list "query"\t (query using server list)\n\t\tquery list.base "query"\t (query using database in list)'
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
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		except KeePassError as e:
			print('--------------------')
			print('ERROR:', e)
			print('--------------------')

	# ------------------------------------------------------------------------------------------------------------------

	def exe_dump(self, file_name, serv_name, base_name, backup_name, type):
		date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		dump_file_name = backup_name+'_'+file_name+'_'+serv_name+'_'+base_name+'_'+date
		dumper = """pg_dump.exe -U %s -d %s -h %s -p %s -f %s -C --column-inserts"""

		try:
			conf = ConfigManager("config/" + file_name + ".yaml")
			cnf = conf.get(serv_name)
			conn = cnf["connection"]
			db = cnf["databases"][base_name]

			db_name = db["name"]
			db_user = db["user"]
			db_pass = conf.get_password(serv_name + '.' + base_name)
			conn_adr = ''
			conn_port = None

			if conn["type"] == "ssh": #Dla połączeń ssh
				cmd = self.connect_command_builder(conn, 'no')
				common.conn.send(cmd)
				ans = None
				while ans == None:
					ans = common.conn.get_state()

				status, hostname, db_port = ans.split("_")

				if status == "ok":  #udało się utworzyć tunel
					conn_adr = 'localhost'
					conn_port = db_port
				else:
					raise PostgressError('Unable to create ssh tunnel')

			elif conn["type"] == "direct":
				conn_adr = conn["adress"]
				conn_port = conn["remoteport"]

			local_version = self.get_local_version('pg_dump --version')
			remote_version = self.get_pg_version(db_name, db_user, db_pass, conn_adr, conn_port)
			if not self.is_valid_versions(local_version, remote_version):
				raise PostgressError("You have too old version of pg_dump")

			if type == 'tar':
				dumper += ' -Ft'
				dump_file_name += '.tar'
			else:
				dump_file_name += '.sql'
			command = dumper % (db_user, db_name, conn_adr, conn_port, dump_file_name)

			os.putenv('PGPASSWORD', db_pass)
			try:
				common.set_cdir_and_store()
				proc = Popen(command, stdout=PIPE, stderr=PIPE)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_dump not found")
			finally:
				common.restore_cdir()
			out, err = proc.communicate()

			if err != b'':
				raise PostgressError(err.decode('utf8', 'ignore'))

		except ConnectionRefusedError:
			print('--------------------')
			print('ERROR: Connection Refused by host')
			print('--------------------')
		except TimeoutError:
			print('--------------------')
			print('ERROR: Connection timeout')
			print('--------------------')
		except paramiko.ssh_exception.AuthenticationException:
			print('--------------------')
			print('ERROR: Authentication problem')
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		except PostgressError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except Exception as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')

	def do_dump(self, args):
		'Dump database and save with name\n\tUsage:\tdump name \t\t(dump using all server lists)\n\t\tdump list name \t\t(dump using server list)\n\t\tdump list.base name \t(dump using database in list)'
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
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		finally:
			common.restore_cdir()

	def do_dump_tar(self, args):
		"Dump database and save with name as tar file\n\tUsage:\tdump name \t\t(dump using all server lists)\n\t\tdump list name \t\t(dump using server list)\n\t\tdump list.base name \t(dump using database in list)"
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
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		except KeePassError as e:
			print('--------------------')
			print('ERROR:', e)
			print('--------------------')
		finally:
			common.restore_cdir()
# ----------------------------------------------------------------------------------------------------------------------

	def restore(self, db_name, db_user, db_pass, host, port, file_name, type = 'sql'):
		if type == 'tar': #jeżeli restorujemy tar'a
			restorer = "pg_restore -U %s -d %s -h %s -p %s"
			command = restorer % (db_user, db_name, host, port)
			os.putenv('PGPASSWORD', db_pass)

			common.set_cdir_and_store()
			bytes_read = open(file_name, "rb")
			common.restore_cdir()

			try:
				proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=bytes_read)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_restore not found")

			out, err = proc.communicate()

			if err != b'':
				raise PostgressError(err.decode('utf8', 'ignore'))

		else:
			restorer = "psql -U %s -d %s -h %s -p %s"
			command = restorer % (db_user, db_name, host, port)
			os.putenv('PGPASSWORD', db_pass)

			common.set_cdir_and_store()
			bytes_read = open(file_name, "rb")
			common.restore_cdir()

			try:
				proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=bytes_read)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_restore not found")

			out, err = proc.communicate()

			if err != b'':
				raise PostgressError(err.decode('utf8', 'ignore'))

	def exe_restore(self, file_name, serv_name, base_name, backup_name, type):

		try:
			conf = ConfigManager("config/" + file_name + ".yaml")
			cnf = conf.get(serv_name)
			conn = cnf["connection"]
			db = cnf["databases"][base_name]

			db_name = db["name"]
			db_user = db["user"]
			db_pass = conf.get_password(serv_name + '.' + base_name)
			conn_adr = ''
			conn_port = None

			if conn["type"] == "ssh": #Dla połączeń ssh
				cmd = self.connect_command_builder(conn, 'no')
				common.conn.send(cmd)
				ans = None
				while ans == None:
					ans = common.conn.get_state()

				status, hostname, db_port = ans.split("_")

				if status == "ok":  #udało się utworzyć tunel
					conn_adr = 'localhost'
					conn_port = db_port
				else:
					raise PostgressError('Unable to create ssh tunnel')

			elif conn["type"] == "direct":
				conn_adr = conn["adress"]
				conn_port = conn["remoteport"]

			local_version = self.get_local_version('pg_dump --version')
			remote_version = self.get_pg_version(db_name, db_user, db_pass, conn_adr, conn_port)
			if not self.is_valid_versions(local_version, remote_version):
				raise PostgressError("You have too old version of pg_dump")

			self.restore(db_name, db_user, db_pass, conn_adr, conn_port, backup_name, type)

		except ConnectionRefusedError:
			print('--------------------')
			print('ERROR: Connection Refused by host')
			print('--------------------')
		except TimeoutError:
			print('--------------------')
			print('ERROR: Connection timeout')
			print('--------------------')
		except paramiko.ssh_exception.AuthenticationException:
			print('--------------------')
			print('ERROR: Authentication problem')
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		except PostgressError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except Exception as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')

	def do_restore(self, args):
		"Restore database from file\n\tUsage:\trestore file \t\t(restore to all server lists)\n\t\trestore list file \t\t(restore to server list)\n\t\trestore list.base file \t(restore to database in list)"
		try:
			(values, num) = self.parse_args(args, 1, 2)

			if num == 2:
				common.set_cdir_and_store()
				if tarfile.is_tarfile(values[1]):
					type = 'tar'
				else:
					type = 'sql'
				common.restore_cdir()

				self.exec_on_config(self.exe_restore, [values[1], type], values[0], 'tree')
			elif num == 1:
				common.set_cdir_and_store()
				if tarfile.is_tarfile(values[0]):
					type = 'tar'
				else:
					type = 'sql'
				common.restore_cdir()

				self.exec_on_config(self.exe_restore, [values[0], type], '', 'tree')

		except ConfigManagerError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except ParseArgsException as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except KeyError as e:
			print('--------------------')
			print('ERROR: Unable to find key:',e)
			print('--------------------')
		except PostgressError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		except FileNotFoundError as e:
			print('--------------------')
			print('ERROR:',e)
			print('--------------------')
		finally:
			common.restore_cdir()

	def complete_query(self, text, line, begidx, endidx):
		if not text:
			completions = self.file_server_database[:]
		else:
			completions = [f for f in self.file_server_database if f.startswith(text)]
		return completions

	def complete_dump(self, text, line, begidx, endidx):
		if not text:
			completions = self.file_server_database[:]
		else:
			completions = [f for f in self.file_server_database if f.startswith(text)]
		return completions

	def complete_dump_tar(self, text, line, begidx, endidx):
		if not text:
			completions = self.file_server_database[:]
		else:
			completions = [f for f in self.file_server_database if f.startswith(text)]
		return completions

	def complete_restore(self, text, line, begidx, endidx):
		if not text:
			completions = self.file_server_database[:]
		else:
			completions = [f for f in self.file_server_database if f.startswith(text)]
		return completions

class PostgressError(Exception):
	def __init__(self, value):
		self.value = value

def init(warn):
	postgres = Postgres()
	postgres.warn = warn
	postgres.cmdloop()