from prettytable import from_db_cursor
from mod_core import ModuleCore, ParseArgsException
import common
from configmanager import ConfigManager, ConfigManagerError
import psycopg2
import os
import paramiko
import datetime
from subprocess import Popen, PIPE

class Postgres(ModuleCore):
	def __init__(self, completekey='tab', stdin=None, stdout=None):
		super().__init__()
		self.set_name('Postgres')
		self.warn = False

	def do_query(self, args):
		try:
			(values, values_num) = self.parse_args(args, 1, 2)

			if values_num == 2:  #wyróżniamy do czego chcemy się połączyć
				conn_params = values[0].split('.')
				if len(conn_params) == 3:  #połącz do konkretnej bazy na liście
					self.query(conn_params[0], conn_params[1], conn_params[2], values[1])

				elif len(conn_params) == 2:  #połącz do konkretnego serwera na liście
					conf = ConfigManager("config/" + conn_params[0] + ".yaml").get(conn_params[1])
					databases = conf["databases"]  #konfiguracje baz danych
					# print(dbs)
					for db in databases:
						print('[', db, ']')
						self.query(conn_params[0], conn_params[1], db, values[1])
						print()

				elif len(conn_params) == 1:  #połącz do wszystkiego na liście
					servers = ConfigManager("config/" + conn_params[0] + ".yaml").get_all()
					for srv in servers:
						databases = servers[srv]["databases"]
						for db in databases:
							print('[', srv, '->', db, ']')
							self.query(conn_params[0], srv, db, values[1])
							print()
				else:
					raise ParseArgsException("Niepoprawny parametr połączenia!")
			elif values_num == 1:  #wykonujemy na wszystkich
				files = []
				for file in os.listdir("./config"):
					if file.endswith(".yaml"):
						files.append(file.split(".")[0])

				print("Query to:")
				for file in files:
					print('+-',file)

				ans = input("Are you sure? [NO/yes/info]: ")
				if ans == "yes":
					for file in files:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							databases = servers[srv]["databases"]
							for db in databases:
								print('[', file, '->', srv, '->', db, ']')
								self.query(file, srv, db, values[0])
								print()

				elif ans == "info":
					for file in files:
						print('+-', file)
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print('|  +-', srv)
							databases = servers[srv]["databases"]
							for db in databases:
								print('|  |  +-', db)
				else:
					print("aborted")

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
			return False

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

	def query(self, file_name, serv_name, base_name, db_query):
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
			pass

	def local_dump(self, db_name, db_user, db_pass, host, port, file_name, type = ''):
		dumper = """./bin/pg_dump.exe -U %s -d %s -h %s -p %s -f %s -C --column-inserts""" + ' ' + type
		command = dumper % (db_user, db_name, host, port, file_name)

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




	def dump(self, file_name, serv_name, base_name, dump_file, type = ''):
		try:
			date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
			cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
			conn = cnf["connection"]
			database = cnf["databases"][base_name]
			dump_file_name = 'dump/'+dump_file+'_'+file_name+'_'+serv_name+'_'+base_name+'_'+date+'.sql'

			os.putenv('PGPASSWORD', database["passwd"])

			if conn["type"] == "ssh": #Dla połączeń ssh
				dumper = "pg_dump -U %s -d %s -C --column-inserts" + ' ' + type
				command = dumper % (database["user"], database["name"])
				client = paramiko.SSHClient()
				client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				client.connect(conn["adress"], username=conn["user"] ,password=conn["passwd"], port=22)
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
					file = open(dump_file_name, 'w')
					file.write(stdout.decode())
					file.close()
				else:
					if self.warn == True:
						print('--------------------')
						print('WARNING: '+stderr.decode('iso_8859_2', 'ignore')+'attempt to use the local pg_dump')
					cmd = conn["adress"] + "_" + conn["user"] + "_" + conn["passwd"] + "_" + str(conn["sshport"]) + "_" + str(conn["remoteport"]) + "_no"
					common.conn.send(cmd)
					ans = None
					while ans == None:
						ans = common.conn.get_state()

					if ans.split('_')[0] == 'ok':
						self.local_dump(database["name"], database["user"], database["passwd"], '127.0.0.1', int(ans.split("_")[2]), dump_file_name, type)
						if self.warn == True:
							print('SUCCESS')
							print('--------------------')
					else:
						if self.warn != True:
							print('--------------------')
						print('FAIL')
						print('--------------------')


			elif conn["type"] == "direct": #Jeżeli nie ma ssh
				self.local_dump(database["name"], database["user"], database["passwd"], conn["adress"], conn["remoteport"], dump_file_name, type)

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

		return True

	def do_dump(self, args):
		"""dump <base> <file_name>"""
		self.dumper(args)

	def do_dump_tar(self, args):
		"""dump <base> <file_name>"""
		self.dumper(args, '-Ft')

	def dumper(self, args, type = ''):
		try:
			(values, values_num) = self.parse_args(args, 1, 2)
			if len(values) == 2: #Jeżeli 2 argumenty (na wybranym konfigu)
				conf_args = values[0].split('.')

				if len(conf_args)== 3:
					self.dump(conf_args[0], conf_args[1], conf_args[2], values[1], type)
				elif len(conf_args) == 2:
					conf = ConfigManager("config/" + conf_args[0] + ".yaml").get(conf_args[1])
					databases = conf["databases"]  #konfiguracje baz danych
					print(">Dumping databases:")
					for db in databases:
						print("+-", db)
						self.dump(conf_args[0], conf_args[1], db, values[1], type)
				elif len(conf_args) == 1:
					servers = ConfigManager("config/" + conf_args[0] + ".yaml").get_all()
					print(">Dumping databases:")
					for srv in servers:
						print("+-", srv)
						databases = servers[srv]["databases"]
						for db in databases:
							print("|  +-", db)
							self.dump(conf_args[0], srv, db, values[1], type)
			elif len(values) == 1: #jeden argument (na wszystkich konfigach)
				files = []
				for file in os.listdir("./config"):
					if file.endswith(".yaml"):
						files.append(file.split(".")[0])

				print("Dump:")
				for file in files:
					print('+-', file)

				ans = input("Are you sure? [NO/yes/info]: ")
				if ans == "yes":
					for file in files:
						print('+-', file)
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("|  +-", srv)
							databases = servers[srv]["databases"]
							for db in databases:
								print("|  |  +-", db)
								self.dump(file, srv, db, values[0])
				elif ans == "info":
					for file in files:
						print('+-', file)
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("|  +-", srv)
							databases = servers[srv]["databases"]
							for db in databases:
								print("|  |  +-", db)
				else:
					print("aborted")
		except ParseArgsException as e:
			print("Incorrect number of arguments.")
		except Exception as e:
			print(e)

	def local_restore(self, db_name, db_user, db_pass, host, port, file_name):
		pass
		# os.putenv('PGPASSWORD', db_pass)
		# dumper = "psql %s -U %s -h %s -p %s"
		# command = dumper % (db_name, db_user, host)
		# client = paramiko.SSHClient()
		# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		# client.connect(conn["adress"], username=conn["user"] ,password=conn["passwd"], port=22)
		# channel = client.get_transport().open_session()
		#
		#
		# channel.exec_command(command)
		#
		# stderr = b''
		# cmd = channel.recv_stderr(256)
		# while cmd != b'':
		# 	stderr += cmd
		# 	cmd = channel.recv_stderr(256)
		#
		# if stderr == b'':
		# 	stdout = b''
		# 	cmd = channel.recv(256)
		# 	while cmd != b'':
		# 		stdout += cmd
		# 		cmd = channel.recv(256)
		# 	file = open(dump_file_name, 'w')
		# 	file.write(stdout.decode())
		# 	file.close()

	def restore(self, file_name, serv_name, base_name, dump_file):
		with open (dump_file, "r") as myfile:
			data=myfile.read()



	def do_restore(self, args):
		try:
			(values, values_num) = self.parse_args(args, 2)
			if len(values) == 2: #Jeżeli 2 argumenty (na wybranym konfigu)
				conf_args = values[0].split('.')
				if len(conf_args)== 3:
					self.restore(conf_args[0], conf_args[1], conf_args[2], values[1])
				else:
					print('ERROR!!!!!')


		except Exception as e:
			print(type(e))
			print(e)

	def do_raw_query(self, args):
		try:
			(values, X) = self.parse_args(args, 3)
			[server_name, base_name] = values[1].split('.')
			file_name = values[0]

			try:
				conf = ConfigManager(file_name).get(server_name)
				adr = conf["connection"]["adress"]
				pwd = conf[base_name]["passwd"]
				usr = conf[base_name]["user"]
				db_name = conf[base_name]["name"]

				try:
					conn = psycopg2.connect(dbname=db_name, user=usr, host=adr, password=pwd, port=5432)
					conn.autocommit = True;
					cur = conn.cursor()
					cur.execute(values[2])

					return cur.fetchall();

				except psycopg2.Error as e:
					print('Error: ', e)
				except psycopg2.Warning as w:
					print('Warning: ', w)
				except psycopg2.InterfaceError as e:
					print('Error: ', e)
				except psycopg2.DatabaseError as e:
					print('Error: ', e)

			except ConfigManagerError as e:
				print(e)
			except Exception as e:
				print(e)


		except ParseArgsException as e:
			print(e)
		except Exception as e:
			print(e)

class PostgressError(Exception):
	def __init__(self, value):
		self.value = value