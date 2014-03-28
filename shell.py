import cmd
import sys
import alias
from tunel import TunnelManager 
sys.path.append("dbmodules")

manager = TunnelManager()

def set_module(module):
    try:
	    exec("get_module('{0}').{1}('{1}').cmdloop()".format(module.lower(), module))
    except:
        print("Nie można wczytać modułu:", module)


def get_module(module):
	return __import__(module)

class Shell(cmd.Cmd):
    prompt = "#>"
    
    def do_exit(self,*args):
        return True

    def do_module(self, module):
        set_module(module)

    def do_connect(self,server):
        """Connecting via ssh"""
        manager.connectToAlias(server)
    def do_listConnections(self,server):
        """list ssh connections"""
        for connection in manager.lista:
            print (connection)

    def do_EOF(self, line):
        return True

    def emptyline(self):
        return False

# if __name__ == '__main__':
try:
    Shell().cmdloop()
except KeyboardInterrupt:
    print("")
    pass