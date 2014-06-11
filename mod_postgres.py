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
				try:
					pg_conn = psycopg2.connect(dbname=database["name"], user=database["user"], host=adr,
											   password=database["passwd"], port=db_port)
					pg_conn.autocommit = True;
					cur = pg_conn.cursor()
					cur.execute(db_query)

					pt = from_db_cursor(cur)
					if (pt != None):
						print(pt)
				except psycopg2.Error as e:
					print('Error: ', e)
				except psycopg2.Warning as w:
					print('Warning: ', w)
				except psycopg2.InterfaceError as e:
					print('Error: ', e)
				except psycopg2.DatabaseError as e:
					print('Error: ', e)
			else:	#próba bezpośredniego połączonia
				pass

			pass
		else:
			pass

	def local_dump(self, db_name, db_user, db_pass, host, port, file_name):
		# os.putenv('PGPASSWORD', db_pass)
		# dumper = """ "./bin/pg_dump.exe" -U %s -d %s -h %s -p %s -f %s -C --column-inserts"""
		# command = dumper % (db_user, db_name, host, port, file_name)
		# call(command, shell=True)

		dumper = """./bin/pg_dump.exe -U %s -d %s -h %s -p %s -f %s -C --column-inserts"""
		command = dumper % (db_user, db_name, host, port, file_name)

		os.putenv('PGPASSWORD', db_pass)
		try:
			proc = Popen(command, stdout=PIPE, stderr=PIPE)
		except FileNotFoundError:
			raise PostgressError("\t\tERROR: pg_dump not found")

		stderr = b'';
		for line in proc.stderr:
			stderr += line

		if stderr != b'':
			raise PostgressError(stderr.decode('iso_8859_2', 'ignore'))




	def dump(self, file_name, serv_name, base_name, dump_file):
		try:
			date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
			cnf = ConfigManager("config/" + file_name + ".yaml").get(serv_name)
			conn = cnf["connection"]
			database = cnf["databases"][base_name]
			dump_file_name = 'dump/'+dump_file+'_'+file_name+'_'+serv_name+'_'+base_name+'_'+date+'.sql'

			os.putenv('PGPASSWORD', database["passwd"])

			if conn["type"] == "ssh": #Dla połączeń ssh
				dumper = "pg_dump -U %s -d %s -C --column-inserts"
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
						print('\t\tWARNING: '+stderr.decode('iso_8859_2', 'ignore')+'\n\t\t\tattempt to use the local pg_dump')

					cmd = conn["adress"] + "_" + conn["user"] + "_" + conn["passwd"] + "_" + str(conn["sshport"]) + "_" + str(conn["remoteport"]) + "_no"
					common.conn.send(cmd)
					ans = None
					while ans == None:
						ans = common.conn.get_state()

					if ans.split('_')[0] == 'ok':
						self.local_dump(database["name"], database["user"], database["passwd"], '127.0.0.1', int(ans.split("_")[2]), dump_file_name)
						if self.warn == True:
							print("\t\tSUCCESS\n")
					else:
						if self.warn == True:
							print("\t\tFAIL\n")


			elif conn["type"] == "direct": #Jeżeli nie ma ssh
				self.local_dump(database["name"], database["user"], database["passwd"], conn["adress"], conn["remoteport"], dump_file_name)

		except ConnectionRefusedError:
			print("\t\tERROR: Connection Refused by host\n")
			return False

		except TimeoutError:
			print("\t\tERROR: Connection timeout\n")
			return False

		except PostgressError as e:
			print(e)
			return False

		except Exception as e:
			print(type(e))
			print(e)
			return False

		return True



	def do_dump(self, args):
		"""dump <base> <file_name>"""
		try:
			(values, values_num) = self.parse_args(args, 1, 2)
			if len(values) == 2: #Jeżeli 2 argumenty (na wybranym konfigu)
				conf_args = values[0].split('.')

				if len(conf_args)== 3:
					self.dump(conf_args[0], conf_args[1], conf_args[2], values[1])
				elif len(conf_args) == 2:
					conf = ConfigManager("config/" + conf_args[0] + ".yaml").get(conf_args[1])
					databases = conf["databases"]  #konfiguracje baz danych
					print(">Dumping databases:")
					for db in databases:
						print("\t" + db)
						self.dump(conf_args[0], conf_args[1], db, values[1])
				elif len(conf_args) == 1:
					servers = ConfigManager("config/" + conf_args[0] + ".yaml").get_all()
					print(">Dumping databases:")
					for srv in servers:
						print("\t" + srv)
						databases = servers[srv]["databases"]
						for db in databases:
							print("\t\t" + db)
							self.dump(conf_args[0], srv, db, values[1])
			elif len(values) == 1: #jeden argument (na wszystkich konfigach)
				files = []
				for file in os.listdir("./config"):
					if file.endswith(".yaml"):
						files.append(file.split(".")[0])

				print("Dump:")
				for file in files:
					print(file)

				ans = input("Are you sure? [NO/yes/info]: ")
				if ans == "yes":
					for file in files:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("\t" + srv)
							databases = servers[srv]["databases"]
							for db in databases:
								print("\t\t" + db)
								self.dump(file, srv, db, values[0])
				elif ans == "info":
					for file in files:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("\t" + srv)
							databases = servers[srv]["databases"]
							for db in databases:
								print("\t\t" + db)
				else:
					print("aborted")
		except ParseArgsException as e:
			print("Incorrect number of arguments.")
		except Exception as e:
			print(e)

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
						print("[" + db + "]")
						self.query(conn_params[0], conn_params[1], db, values[1])
						print()
				elif len(conn_params) == 1:  #połącz do wszystkiego na liście
					servers = ConfigManager("config/" + conn_params[0] + ".yaml").get_all()
					for srv in servers:
						print("[---- " + srv + " ----]")
						databases = servers[srv]["databases"]
						for db in databases:
							print("+[" + db + "]")
							self.query(conn_params[0], srv, db, values[1])
							print()
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
					print(file)

				ans = input("Are you sure? [NO/yes/info]: ")
				if ans == "yes":
					for file in files:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("[---- " + srv + " ----]")
							databases = servers[srv]["databases"]
							for db in databases:
								print("+[" + db + "]")
								self.query(file, srv, db, values[0])
								print()
						print()
				elif ans == "info":
					for file in files:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							print("[---- " + srv + " ----]")
							databases = servers[srv]["databases"]
							for db in databases:
								print("+" + db)
						print()
					print()
				else:
					print("aborted")

		except ConfigManagerError as e:
			print(e)
		except ParseArgsException as e:
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