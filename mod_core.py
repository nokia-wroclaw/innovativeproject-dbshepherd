import cmd
import re
from configmanager import  ConfigManager, ConfigManagerError


class ParseArgsException(Exception):
	def __init__(self, msg):
		self.msg = msg

class ModuleCore(cmd.Cmd):
	def set_name(self, name):
		self.prompt = "[" + name + "]>"

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
		from getpass import getpass
		import sys
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