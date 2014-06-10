import os
import unittest
from configmanager import ConfigManager, ConfigManagerError


def connect_command_builder(connection, perm):
		command = connection["adress"] + "_" + connection["user"]+ "_" + \
					connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_" + perm
		return command
def send_command(command):
	try:
		conn.send(command)
		t = None
		while t == None:
			t = conn.get_state()
		return t
	except AttributeError as e:
		print (e)

class YamlTest(unittest.TestCase):

	def test1_valid_yaml_file(self):
		lists = []
		for file in os.listdir("config"):
					if file.endswith(".yaml"):
						list_name = file.title()[:file.rfind(".")]
						if list_name != "Lista_Test":
							lists.append(list_name)
		for file in lists:
			try:
				yaml = ConfigManager("config/"+file+".yaml")
			except ConfigManagerError:
				self.fail(file)
		
	def test2_have_valid_connections(self):
		lists = []
		for file in os.listdir("config"):
					if file.endswith(".yaml"):
						list_name = file.title()[:file.rfind(".")]
						if list_name != "Lista_Test":
							lists.append(list_name)
		for file in lists:
			try:
				yaml = ConfigManager("config/"+file+".yaml")
				for server in yaml.loader:
					try:
						connection = yaml.get(server)["connection"]
						test = connection["adress"]
						test = connection["type"]
						if test == "ssh":
							test = connection["sshport"]
						test = connection["remoteport"]
						test = connection["user"]
						test = connection["passwd"]
					except KeyError as e:
						self.fail(str(e) + " in " + server + "(" + file + ")")
	
			except ConfigManagerError:
				self.fail(file)	
	
				
if __name__ == '__main__':
	unittest.main(verbosity=2)#