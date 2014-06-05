import unittest
import connection
from ssh_tunnelmanager import TunnelManager
from configmanager import ConfigManager, ConfigManagerError
conn = None 

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

class SShTest(unittest.TestCase):

	def test_connection_to_ssh_shepherd(self):
		self.assertIsNotNone(conn)
	
	def test_invalid_yaml_connection(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("InvalidConnection")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError:
			cmd = None
		self.assertIsNone(cmd)
	
	def test_invalid_ssh_port(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("InvalidSSHPort")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError as e:
			self.fail("KeyError" + e)
		
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("bad", status)
	
	def test_invalid_user_name(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("InvalidUsername")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError as e:
			self.fail("KeyError" + e)
		
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("bad", status)
	
	def test_should_be_ok(self):
		conf = ConfigManager("config/lista_test.yaml")
		connection =  conf.get("ShouldBeOK")["connection"]
		try:
			cmd = connect_command_builder(connection,"no")
		except KeyError as e:
			self.fail("KeyError" + e)
		
		ans = send_command(cmd)
		status = ans.split("_")[0]
		self.assertEqual("ok", status)
	
if __name__ == '__main__':
	try:
		conn = connection.Connection()
		conn.start()
	except ConnectionRefusedError:
		print("is ssh-shepherd running?")
			
	unittest.main(verbosity=2)