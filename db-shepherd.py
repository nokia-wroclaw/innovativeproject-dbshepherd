import os
import cmd
import common
import configparser
from sys import modules
from os.path import splitext
from kp import KeePassError
from ssh_tunnelmanager import TunnelManager
from mod_core import ParseArgsException, ModuleCore
from configmanager import ConfigManager, ConfigManagerError

conn = common.conn
keepass_path = common.keepass_path
dump_path = common.dump_path
config_path = common.config_path
common.app_dir = os.getcwd()
common.current_dir = os.getcwd()

manager = TunnelManager()

def init():
	global keepass_path, dump_path, config_path
		
	config = configparser.ConfigParser()
	try:
		config.read_file(open('conf.cfg'))
		try:
			keepass_path = config.get('global', 'keepass_path')
			dump_path = config.get('global', 'dump_path')
			config_path = config.get('global', 'config_path')
		except configparser.NoOptionError as e:
			print (e)
			exit(123)
		except configparser.NoSectionError as e:
			print (e)
			exit(124)
	except FileNotFoundError as e:
		print (e)	
		exit(125)
		
	if not os.path.isdir(dump_path):
		print("Unable to find dump directory")
	if not os.path.isdir(config_path):
		print("Unable to find configuration directory")
	if not os.path.exists(keepass_path):
		print("Unable to find keepass file")

def exit(int):
	import sys
	if conn != None:
		conn.stop()
	sys.exit(int)	
	
def send_command(command):
	try:
		conn.send(command)
		t = None
		while t == None:
			t = conn.get_state()
		return t
	except AttributeError as e:
		print (e)

def set_module(module, warn):
	try:
		if len(module) > 0:
			module_src = splitext(ConfigManager("modules.yaml").get(module)['source'])[0]
			__import__(module_src)
			exec("mod = modules['{0}'].{1}()\nmod.warn={2}\nmod.cmdloop()".format(module_src,module, warn))
		else:
			print("Musisz podać nazwę modułu!")
	except ImportError as e:
		print(e)
	except ConfigManagerError as e:
		print("Can't load [" + module + "] check modules.yaml")

		
class Shell(ModuleCore):
	def __init__(self):
		super().__init__(module='#')
		self.warn = False
		self.do_logo()
		self.modules = []
		self.do_cd('.')

		try:
			loader = ConfigManager("modules.yaml").get_list()
			for module_name in loader:
				self.modules.append(module_name)
		except ConfigManagerError as e:
			print(e)

	def do_exit(self, *args):
		"Exit db-shepherd"
		return True

	def do_module(self, module):
		"Load module\n\tUsage:\t module <Module>\t(load and use Module)"
		set_module(module, self.warn)
		self.do_cd('.')

	def do_connect(self, arg):
		"""Create ssh tunnels\n\tUsage:\tconnect\t\t\t(connect using all server lists)
		connect list\t\t(connect using list)
		connect list.server\t(connect to server from list)"""
		if arg == "": # if no args connect to all
			print ("Connect to all")
			ans = input("Are you sure?[NO/yes/info]: ")
			lists = []
			for file in os.listdir("config"):
					if file.endswith(".yaml"):
						list_name = file.title()[:file.rfind(".")]
						lists.append(list_name)

			if ans == "info":
				print ("Lists with servers to connect:")
				for l in lists:
					print(l)
			elif ans == "yes":
				for l in lists:
					print("Connecting(",l,")")
					self.connectList("config/" + l + ".yaml")
			else:
				print("Aborted")

		else:
			params = arg.split(".")
			if len(params) == 1:
				print ("connect list...")
				self.connectList("config/"+params[0]+".yaml")
			elif len(params) == 2:
				print ("connect serv...")
				try:
					conf = ConfigManager("config/"+params[0]+".yaml")
					connection =  conf.get(params[1])["connection"]
					command = self.connect_command_builder(connection,"no")
					try:
						conn.send(command)
						t = None
						while t == None:
							t = conn.get_state()
						print(t)
					except AttributeError as e:
						print("Connection to ssh shepherd error!",e)
				except ConfigManagerError as e:
					print (e)
				except KeePassError as e:
					print("Connecting to" , connection["adress"], "[", e, "]")
				except Exception as e:
					print (e)
			else:
				print ("error")

	def do_perm(self,arg):
		"Create permament ssh tunnel\n\tUsage:\tperm <list>.<server>\t(make permament tunnel to server)"
		params = arg.split(".")
		conf = ConfigManager("config/"+params[0]+".yaml")
		try:
			connection =  conf.get(params[1])["connection"]
			ret = send_command(self.connect_command_builder(connection,"yes"))
			print (ret)
		except KeePassError as e:
			print("Connecting to" , connection["adress"], "[", e, "]")

	def do_disconnect(self, arg):
		"""Close tunnel to server\n\tUsage:\tdisconnect;server:port(;server:port;...)
					(disconect form servers)"""
		command = "clean;" + arg
		ret = send_command(command)
		print (ret)

	def do_list(self ,arg):
		"Print all created tunnels"
		ret = send_command("list")
		print (ret)

	def do_EOF(self, line):
		return True

	def emptyline(self):
		return False

	def complete_module(self, text, line, begidx, endidx):
		if not text:
			completions = self.modules[:]
		else:
			completions = [f for f in self.modules if f.startswith(text)]
		return completions

	def connectList(self, listFile):
		try:
			conf = ConfigManager(listFile)
		except Exception as e:
			print ("No conf file", listFile)
			return 1

		server_list = []
		for server in conf.get_list():
			server_list.append(server)

		connection_list ={}
		for server in server_list:
			connection =  conf.get(server)["connection"]
			try:
				command = self.connect_command_builder(connection,"no")
				try:
					conn.send(command)
					t = None
					while t == None:
						t = conn.get_state()
						#status_adres_localport
					server_status = t.split("_")
					try:
						connection_list[server_status[1]]=server_status[2]
						print("Connecting to" , connection["adress"], "[", server_status[0], "]")
					except IndexError as e:
						print(t)
				except AttributeError as e:
					print("Connection to ssh shepherd error!",e)
			except KeePassError as e:
				print("Connecting to" , connection["adress"], "[", e, "]")
			except KeyError as e:
				print("Connecting to" , connection["adress"], "[", e, "]")
			except Exception as e:
					print (e)	

	def complete_connect(self, text, line, begidx, endidx):
		if not text:
			completions = self.file_server[:]
		else:
			completions = [f for f in self.file_server if f.startswith(text)]
		return completions

	def do_logo(self, args = ''):
		"Print db-shepherd logo"
		ts = os.get_terminal_size()
		space = (ts.columns - 66) / 2

		logo ="""       ____               __               __                  __
  ____/ / /_        _____/ /_  ___  ____  / /_  ___  _________/ /
 / __  / __ \______/ ___/ __ \/ _ \/ __ \/ __ \/ _ \/ ___/ __  /
/ /_/ / /_/ /_____(__  ) / / /  __/ /_/ / / / /  __/ /  / /_/ /
\__,_/_.___/     /____/_/ /_/\___/ .___/_/ /_/\___/_/   \__,_/
                                /_/                              """
		logo_lines = logo.split('\n')
		for line in logo_lines:
			print(' ' * int(space)  + line)


# if __name__ == '__main__':
try:
	init()
	Shell().cmdloop()
	if conn != None:
		conn.stop()
		
except KeyboardInterrupt:
	if conn != None:
		conn.stop()
	print("")