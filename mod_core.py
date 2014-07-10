import re
import os
import cmd
import sys
import common
from getpass import getpass
from kp import KeePassError, get_password 
from configmanager import  ConfigManager, ConfigManagerError

common.init()
keepass_path = common.keepass_path

class ParseArgsException(Exception):
	def __init__(self, msg):
		self.msg = msg

class ModuleCore(cmd.Cmd):
	def __init__(self, module = ''):
		cmd.Cmd.__init__(self)
		self.master = None

		if module == '#':
			self.prompt_sign = '#>'
		elif module != '':
			self.prompt_sign = '[' + module + ']>'
		else:
			self.prompt_sign = '->'

		#defaults
		self.ruler = '-'

		#Completions
		self.directories = []
		self.file_server_database = []
		self.file_server = []

		self.do_cd('.')

		configs = ConfigManager().get_config_list()
		for conf in configs:
			self.file_server_database.append(conf)
			self.file_server.append(conf)
			for srv in ConfigManager('config/' + conf + '.yaml').get_all():
				self.file_server_database.append(conf + '.' + srv)
				self.file_server.append(conf + '.' + srv)
				for db in ConfigManager('config/' + conf + '.yaml').get(srv)['databases']:
					self.file_server_database.append(conf + '.' + srv + '.' + db)

	def precmd(self, line):
		if not sys.stdin.isatty():
			print(line)
		return line
	
	def postcmd(self, stop, line):
		if not sys.stdin.isatty():
			print("")
		return stop

	def parse_args(self, string="", n=0, m=0):
		list = re.findall('"+.*"+|[a-zA-Z0-9!@#$%^&*()_+-,./<>?]+', string)
		arg_counter = len(list);
		if (arg_counter >= n and arg_counter <= m) or (arg_counter == n and m == 0) or n == 0:
			r_list = []
			for l in list:
				r_list.append(l.replace('"', ''))
			return (r_list, len(list))
		else:
			raise ParseArgsException("Nieodpowiednia ilość argumentów")

	def exec_on_config(self, fun, args, values, view = ''): # link - file.server.base
		if values == '': # wykonaj na wszystkich plikach
			files = ConfigManager().get_config_list() # pobierz listę plików konfiguracyjnych

			print("Exec on:")
			for file in files:
				print('+-',file)

			ans = input("Are you sure? [NO/yes/info]: ")
			if ans == "yes":
				for file in files:
					if view == 'tree': print('+-', file)
					try:
						servers = ConfigManager("config/" + file + ".yaml").get_all()
						for srv in servers:
							if view == 'tree': print("|  +-", srv)
							databases = servers[srv]["databases"]
							for db in databases:
								if view == 'tree': print("|  |  +-", db)
								if view == 'list': print('[', file, '->', srv, '->', db, ']')
								fun(file, srv, db, *args)
					except ConfigManagerError as e:
						print(e)
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

		else:
			val = values.split('.')
			params = len(val)
			if params == 1:
				file = val[0]
				try:
					servers = ConfigManager("config/" + file + ".yaml").get_all()
					for srv in servers:
						if view == 'tree': print("+-", srv)
						databases = servers[srv]["databases"]
						for db in databases:
							if view == 'tree': print("|  +-", db)
							if view == 'list': print('[', srv, '->', db, ']')
							fun(file, srv, db, *args)
				except ConfigManagerError as e:
					print(e)
				except KeyError as e:
					print(e, "is not exist")

			elif params == 2:
				file = val[0]
				try:
					servers = ConfigManager("config/" + file + ".yaml").get_all()
					srv = val[1]
					databases = servers[srv]["databases"]
					for db in databases:
						if view == 'tree': print("+-", db)
						if view == 'list': print('[', db, ']')
						fun(file, srv, db, *args)
				except ConfigManagerError as e:
					print(e)
				except KeyError as e:
					print(e, "is not exist")

			elif params == 3:
				try:
					fun(val[0], val[1], val[2], *args)
				except ConfigManagerError as e:
					print(e)
				except KeyError as e:
					print(e, "is not exist")

	def get_shortpath(self):
		path = common.get_cdir()
		separator = ''
		if '\\' in path:
			separator = '\\'
		else:
			separator = '/'
		start = path.find(separator)
		end = path.rfind(separator, 0, len(path)-1)
		if start < end:
			return (path[0:start+1] + '...' + path[end:])
		else:
			return (path)

	def complete_cd(self, text, line, begidx, endidx):
		if not text:
			completions = self.directories[:]
		else:
			completions = [f for f in self.directories if f.startswith(text)]
		return completions

	def do_cd(self, args):
		"Move to directory"
		if args == '':
			print(common.get_cdir())
		else:
			try:
				common.chdir(args)
				self.prompt = self.get_shortpath() + ' ' + self.prompt_sign

				self.directories = []
				for name in os.listdir(common.get_cdir()):
					if os.path.isdir(os.path.join(common.get_cdir(), name)):
						self.directories.append(name)
			except FileNotFoundError as e:
				print(e)

	def do_ls(self, args):
		"List directory"
		for name in os.listdir(common.get_cdir()):
			print(name)


	def do_pwd(self, args):
		"Print path"
		print(common.get_cdir())

	def do_warn(self, args):
		"""warn <on/off>"""
		try:
			(values, values_num) = self.parse_args(args, 0, 1)
			if values_num == 1:
				if values[0] == 'on':
					print('Warnings on')
					self.warn = True
				elif values[0] == 'off':
					print('Warnings off')
					self.warn = False
				else:
					print('Incorrect argument.')
			else:
				if self.warn == True:
					print('Status: on')
				else:
					print('Status: off')

		except ParseArgsException as e:
			print(e)
	
	def do_setMaster(self,args):
		"Set master password"
		if sys.stdin.isatty(): # jezeli jako shell
			p = getpass('Enter Master Password: ')
		else:
			p = sys.stdin.readline().rstrip()
		self.master = p
		
	def do_exit(self, *args):
		return True

	def do_EOF(self, line):
		return True

	def emptyline(self):
		return False
	
	# Musimy wyłapać wszystko co możliwe, nie ma pliku, zly master itp. i zwrocic 1 wyjątek
	def get_password(self, alias):
		if self.master == None:
			raise KeePassError("Master Password Not Set")
		try:
			return get_password(keepass_path, self.master, alias)
		except KeePassError as e:
			raise e

	def connect_command_builder(self,connection, perm):
		try:
			command = connection["adress"] + "_" + connection["user"]+ "_" + \
					self.get_password(connection["keepass"]) + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_" + perm
		except (KeyError, KeePassError) as e1:
			try:
				command = connection["adress"] + "_" + connection["user"]+ "_" + \
					connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_" + perm
				return command
			except KeyError as e2:
				if isinstance(e1,KeePassError):
					raise KeePassError("Unable to use Keepass(" + e1.value + ") or Password")
				else:
					raise KeePassError("Invalid connection in yaml file")
			raise KeePassError(e1)
		return command