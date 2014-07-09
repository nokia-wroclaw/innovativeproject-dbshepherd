from prettytable import from_db_cursor
from mod_core import ModuleCore, ParseArgsException
import common
from configmanager import ConfigManager, ConfigManagerError
import psycopg2
import os
import paramiko
import datetime
from subprocess import Popen, PIPE
import re
import tarfile

class Postgres(ModuleCore):
	def __init__(self, completekey='tab', stdin=None, stdout=None):
		super().__init__()
		self.set_name('Postgres')
		self.warn = False
		self.do_cd('.')

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

	def exe_dump(self, file_name, serv_name, base_name, backup_name, type):
		date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		dump_file_name = 'dump/'+backup_name+'_'+file_name+'_'+serv_name+'_'+base_name+'_'+date
		dumper = """pg_dump.exe -U %s -d %s -h %s -p %s -f %s -C --column-inserts"""

		try:
			cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
			conn = cnf["connection"]
			db = cnf["databases"][base_name]

			db_name = db["name"]
			db_user = db["user"]
			db_pass = db["passwd"]
			conn_adr = ''
			conn_port = None

			if conn["type"] == "ssh": #Dla połączeń ssh
				cmd = conn["adress"] + "_" + conn["user"] + "_" + conn["passwd"] + "_" + str(conn["sshport"]) + "_" + str(conn["remoteport"]) + "_no"
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
				proc = Popen(command, stdout=PIPE, stderr=PIPE)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_dump not found")
			out, err = proc.communicate()

			if err != b'':
				raise PostgressError(err.decode('utf8', 'ignore'))

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

	def restore(self, db_name, db_user, db_pass, host, port, file_name, type = 'sql'):
		if type == 'tar': #jeżeli restorujemy tar'a
			restorer = "pg_restore -U %s -d %s -h %s -p %s"
			command = restorer % (db_user, db_name, host, port)
			os.putenv('PGPASSWORD', db_pass)

			bytes_read = open(file_name, "rb")

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

			bytes_read = open(file_name, "rb")

			try:
				proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=bytes_read)
			except FileNotFoundError:
				raise PostgressError(" ERROR: pg_restore not found")

			out, err = proc.communicate()

			if err != b'':
				raise PostgressError(err.decode('utf8', 'ignore'))

	def exe_restore(self, file_name, serv_name, base_name, backup_name, type):

		try:
			cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
			conn = cnf["connection"]
			db = cnf["databases"][base_name]

			db_name = db["name"]
			db_user = db["user"]
			db_pass = db["passwd"]
			conn_adr = ''
			conn_port = None

			if conn["type"] == "ssh": #Dla połączeń ssh
				cmd = conn["adress"] + "_" + conn["user"] + "_" + conn["passwd"] + "_" + str(conn["sshport"]) + "_" + str(conn["remoteport"]) + "_no"
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

	def do_restore(self, args):
		try:
			(values, num) = self.parse_args(args, 1, 2)

			if num == 2:
				if tarfile.is_tarfile(values[1]):
					type = 'tar'
				else:
					type = 'sql'
				self.exec_on_config(self.exe_restore, [values[1], type], values[0], 'tree')
			elif num == 1:
				if tarfile.is_tarfile(values[0]):
					type = 'tar'
				else:
					type = 'sql'
				self.exec_on_config(self.exe_restore, [values[0], type], '', 'tree')

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
		except PostgressError as e:
			print(e)


class PostgressError(Exception):
	def __init__(self, value):
		self.value = value