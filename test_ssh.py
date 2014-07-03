import unittest
import connection
from ssh_tunnelmanager import TunnelManager
from configmanager import ConfigManager, ConfigManagerError
from getpass import getpass
from kp import KeePassError, get_password 

conn = None 
master = None

def setUpModule():
	global master
	global conn
	
	try:
		conn = connection.Connection()
		conn.start()
	except ConnectionRefusedError:
		print("is ssh-shepherd running?")
	
	master = getpass("Master pass:")
	
def tearDownModule():
	conn.stop()
	
	
def connect_command_builder(connection, perm):
		command = connection["adress"] + "_" + connection["user"]+ "_" + \
					get_pass(connection["passwd"]) + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_" + perm
		return command
		
def get_pass(alias):
		file = "keys.kdb"
		if master == None:
			raise KeePassError("Master Password Not Set")
		try:
			return get_password(file, master, alias)
		except KeePassError as e:
			print (e)
			raise e

		
def create_command(server,perm):
	conf = ConfigManager("config/lista_test.yaml")
	connection =  conf.get(server)["connection"]
	try:
		cmd = connect_command_builder(connection,perm)
	except KeyError:
		cmd = None
	return cmd
	
def send_command(command):
	try:
		conn.send(command)
		t = None
		while t == None:
			t = conn.get_state()
		return t
	except AttributeError as e:
		print (e)

class SShTest(unittest.TestCase):
	
		

	def test1_connection_to_ssh_shepherd(self):
		self.assertIsNotNone(conn)
	
	def test2_invalid_yaml_connection(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("InvalidConnection")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError:
			cmd = None
		self.assertIsNone(cmd)
	
	def test8_invalid_ssh_port(self):
		cmd =  create_command("InvalidSSHPort","no")
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("bad", status)
	
	def test7_invalid_user_name(self):
		cmd =  create_command("InvalidUsername","no")
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("bad", status)
	
	def test3_should_be_ok(self):
		cmd =  create_command("ShouldBeOK","no")
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("ok", status)
	
	def test6_create_permanent(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("ShouldBeOK")["connection"]
		try:
			cmd = connect_command_builder(connection,"yes")
		except KeyError as e:
			self.fail("KeyError" + e)
	
		ans = send_command(cmd)
		status = ans.split("_")[0]
		if status != "ok":
			self.fail("Unable to create tunnel")
		
		
		to_find = connection["adress"] + ":" + str(connection["remoteport"])
		self.assertEqual(-1, ans.find(to_find,ans.find("perm")))
		
		dc = cmd.split("_")[0] + ":" + cmd.split("_")[4]		
		ans = send_command("clean;" + dc)
		
		
	def test5_disconnect(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("ShouldBeOK")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError as e:
			self.fail("KeyError" + e)
		ans = send_command(cmd)
		status = ans.split("_")[0]
		if status != "ok":
			self.fail("Unable to create tunnel")
		dc = cmd.split("_")[0] + ":" + cmd.split("_")[4]		
		ans = send_command("clean;" + dc)
		to_find = connection["adress"] + ":" + str(connection["remoteport"])
		self.assertEqual(-1, ans.find(to_find))
		
	
	def test4_list_command(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("ShouldBeOK")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError as e:
			self.fail("KeyError" + e)
		ans = send_command(cmd)
		status = ans.split("_")[0]
		
		if status != "ok":
			self.fail("Unable to create tunnel")
		
		ans = send_command("list")
		to_find = connection["adress"] + ":" + str(connection["remoteport"])
		self.assertNotEqual(-1, ans.find(to_find))
		
if __name__ == '__main__':	
	unittest.main(verbosity=2)