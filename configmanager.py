import os
import kp
import yaml
import common

keepass_path = common.keepass_path

class ConfigManager:
	def __init__(self, path = ''):
		if path != '':
			self.path = path
			try:
				self.yamlfile = open(path,'r')
			except FileNotFoundError:
				raise ConfigManagerError(path+' file does not exist')
			self.loader = yaml.load(self.yamlfile)
			self.yamlfile.close()
		
	def get(self, what):
		try:
			return self.loader[what]
		except KeyError:
			err = what + ' is not exist in: '+self.path
			raise ConfigManagerError(err)
	
	def get_list(self):
			return_list = []
			for server in self.loader:
				return_list.append(server)
			return return_list
			
	def get_all(self):
		return self.loader

	def get_config_list(self):
		files = []
		for file in os.listdir("./config"):
			if file.endswith(".yaml"):
				files.append(file.split(".")[0])
		return files

	def get_password(self, alias, master=None):
		splitted_alias = alias.split(".")
		
		if len(splitted_alias) < 1:
			return None
		elif len(splitted_alias) == 1:
			list = self.loader[splitted_alias[0]]["connection"]
			
		else:
			list = self.loader[splitted_alias[0]]["databases"][splitted_alias[1]]
			
		if master != None:
			try:
				return kp.get_password(keepass_path, master, list["keepass"])
			except (KeyError, kp.KeePassError) as e1:
				try:
					return  list["passwd"]
				except KeyError:
					raise ConfigManagerError("Unable to get Password from Keepass or Passwd(" + e1 + ")")
		else:
			try:
				return  list["passwd"]
			except KeyError:
				raise ConfigManagerError("Unable to get Password (MasterPasswordNot set or no Passwd field)")	
		
class ConfigManagerError(Exception):
	def __init__(self, value):
		self.value = value
