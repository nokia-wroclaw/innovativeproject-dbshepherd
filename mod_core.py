import cmd
import re
import sys
from configmanager import  ConfigManager, ConfigManagerError
from getpass import getpass
import os
import re
import common

class ParseArgsException(Exception):
	def __init__(self, msg):
		self.msg = msg

class ModuleCore(cmd.Cmd):
	#Prompt with path
	new_prompt = ''

	#defaults
	ruler = '-'

	#Completions
	directories = []
	file_server_database = []
	file_server = []

	configs = ConfigManager().get_config_list()
	for conf in configs:
		file_server_database.append(conf)
		file_server.append(conf)
		for srv in ConfigManager('config/' + conf + '.yaml').get_all():
			file_server_database.append(conf + '.' + srv)
			file_server.append(conf + '.' + srv)
			for db in ConfigManager('config/' + conf + '.yaml').get(srv)['databases']:
				file_server_database.append(conf + '.' + srv + '.' + db)


	def precmd(self, line):
		if not sys.stdin.isatty():
			print(line)
		return line
	
	def postcmd(self, stop, line):
		if not sys.stdin.isatty():
			print("")
		return stop
		
	def set_name(self, name):
		self.new_prompt = "[" + name + "]>"

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
		c_dir = os.getcwd()
		try:
			os.chdir(common.get_cdir())
			os.chdir(args)
			common.current_dir = os.getcwd()



			self.prompt = self.get_shortpath() + ' ' + self.new_prompt

			self.directories = []
			for name in os.listdir(common.get_cdir()):
				if os.path.isdir(os.path.join(common.get_cdir(), name)):
					self.directories.append(name)

			os.chdir(c_dir)
		except FileNotFoundError as e:
			os.chdir(c_dir)
			print(e)

	def do_path(self, args):
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