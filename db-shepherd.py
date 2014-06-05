import cmd
from sys import modules
from configmanager import ConfigManager, ConfigManagerError
from os.path import splitext
from ssh_tunnelmanager import TunnelManager
import os
import common

conn = common.conn
manager = TunnelManager()

def send_command(command):
	try:
		conn.send(command)
		t = None
		while t == None:
			t = conn.get_state()
		return t
	except AttributeError as e:
		print (e)

def set_module(module):
	try:
		if len(module) > 0:
			module_src = splitext(ConfigManager("modules.yaml").get(module)['source'])[0]
			__import__(module_src)
			exec("modules['{0}'].{1}().cmdloop()".format(module_src,module))
		else:
			print("Musisz podać nazwę modułu!")
	except ImportError as e:
		print(e)
	except ConfigManagerError as e:
		print("Can't load [" + module + "] check modules.yaml")

		
class Shell(cmd.Cmd):
	def __init__(self):
		super().__init__()

	prompt = "#>"
	modules = []

	try:
		loader = ConfigManager("modules.yaml").loader
		for module_name in loader:
			modules.append(module_name)
	except ConfigManagerError as e:
		print(e)

	def do_exit(self, *args):
		"Exit db-shepherd"
		return True

	def do_module(self, module):
		"Load module\n\tUsage:\t module <Module>\t(load and use Module)"
		set_module(module)

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
					command = connection["adress"] + "_" + connection["user"]+ "_" + \
							connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"])+ "_no"
					try:
						conn.send(command)
						t = None
						while t == None:
							t = conn.get_state()
						print(t)
					except AttributeError as e:
						print("CONNECTING USING LOCAL MANAGER!")
				except ConfigManagerError as e:
					print (e)
				
				except Exception as e:
					print (e)
			else:
				print ("error")

	def do_perm(self,arg):
		"Create permament ssh tunnel\n\tUsage:\tperm <list>.<server>\t(make permament tunnel to server)"
		params = arg.split(".")
		conf = ConfigManager("config/"+params[0]+".yaml")
		connection =  conf.get(params[1])["connection"]
		ret = send_command(self.connect_command_builder(connection,"yes"))
		print (ret)

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
		
	def connect_command_builder(self,connection, perm):
		command = connection["adress"] + "_" + connection["user"]+ "_" + \
					connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_" + perm
		return command

	def connectList(self, listFile):
		try:
			conf = ConfigManager(listFile)
		except Exception as e:
			print ("No conf file", listFile)
			return 1
		
		server_list = []
		for server in conf.loader:
			server_list.append(server)

		connection_list ={}
		for server in server_list:
			connection =  conf.get(server)["connection"]
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
				print("CONNECTING USING LOCAL MANAGER!")
		print(connection_list)

# if __name__ == '__main__':
try:
	Shell().cmdloop()
	if conn != None:
		conn.stop()
except KeyboardInterrupt:
	if conn != None:
		conn.stop()
	print("")
	pass