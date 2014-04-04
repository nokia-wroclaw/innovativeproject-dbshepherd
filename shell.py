import cmd
import glob
from imp import find_module
import os
import sys
import alias
from tunel import TunnelManager

sys.path.append("dbmodules")

manager = TunnelManager()


def set_module(module):
    try:
        if len(module) > 0:
            exec("get_module('{0}').{1}('{1}').cmdloop()".format(module.lower(), module))
        else:
            print("Musisz podać nazwę modułu!")
    except:
        print("Nie można wczytać modułu:", module)


def get_module(module):
    return __import__(module)


def is_exist(module):
    try:
        find_module('dbmodules/' + module)
        return True
    except ImportError:
        return False


class Shell(cmd.Cmd):
    prompt = "#>"
    modules = []

    for file in os.listdir("dbmodules"):
        if file.endswith(".py"):
            module_name = file.title()[:file.rfind(".")]
            if is_exist(module_name):
                modules.append(module_name)

    def do_exit(self, *args):
        return True

    def do_module(self, module):
        set_module(module)

    def complete_module(self, text, line, begidx, endidx):
        if not text:
            completions = self.modules[:]
        else:
            completions = [f for f in self.modules if f.startswith(text)]
        return completions

    def do_connect(self, server):
        """Connecting via ssh"""
        manager.connectToAlias(server)

    def do_listConnections(self, server):
        """list ssh connections"""
        for connection in manager.lista:
            print(connection)

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