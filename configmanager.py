import yaml
#najpierw & później * !!

class ConfigManager:
    def __init__(self, path):
        try:
            self.yamlfile = open(path,'r')
        except FileNotFoundError:
            raise ConfigManagerError("No file under this path")
        self.loader = yaml.load(self.yamlfile)

    def show(self, what):
        try:
            return self.loader[what]
        except KeyError:
            err = what + " is not present in yaml file"
            raise ConfigManagerError(err)

class ConfigManagerError(Exception):
    def __init__(self, value):
        self.value = value
