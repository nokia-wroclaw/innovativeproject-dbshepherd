import cmd
import glob
from imp import find_module
import os
import sys
import connection
import configmanager

from sshmodules.tunnelmanager import TunnelManager

# sys.path.append("dbmodules")

manager = TunnelManager()


def set_module(module):
    try:
        if len(module) > 0:
            __import__("dbmodules." + module.lower())
            exec("sys.modules['dbmodules.{0}'].{1}().cmdloop()".format(module.lower(),module))
        else:
            print("Musisz podać nazwę modułu!")
    except ImportError as e:
        print(e)
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
    def __init__(self):
        super().__init__()
        try:
            self.conn = connection.Connection()
            self.conn.start()
        except ConnectionRefusedError:
            print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")

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

    def do_connect(self, arg):
        """Connecting via ssh"""
        self.conn.send(arg)
        t = None
        while t == None:
            t = self.conn.get_state()
        print(t)


    def do_localConnect(self, arg):
        """Connecting via ssh"""
        manager.connectToAlias(arg)

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