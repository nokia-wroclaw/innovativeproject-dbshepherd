import yaml
#najpierw & później * !!

class Alias:
    def __init__(self, path):
        try:
            self.yamlfile = open(path,'r')
        except FileNotFoundError:
            raise AliasError("No file under this path")
        self.loader = yaml.load(self.yamlfile)

    def show(self, what):
        try:
            return self.loader[what]
        except KeyError:
            err = what + " is not present in yaml file"
            raise AliasError(err)

class AliasError(Exception):
    def __init__(self, value):
        self.value = value
