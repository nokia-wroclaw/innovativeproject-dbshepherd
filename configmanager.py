import yaml
import os
#najpierw & później * !!

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

class ConfigManagerError(Exception):
	def __init__(self, value):
		self.value = value
