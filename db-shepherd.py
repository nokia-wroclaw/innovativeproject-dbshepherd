import cmd
from sys import modules #Nie wywalać!
from configmanager import ConfigManager, ConfigManagerError
from os.path import splitext
from ssh_tunnelmanager import TunnelManager

manager = TunnelManager()
import common
conn = common.conn

def set_module(module):
    try:
        if len(module) > 0:
            module_src = splitext(ConfigManager("modules.yaml").show(module)['source'])[0]
            __import__(module_src)
            exec("modules['{0}'].{1}().cmdloop()".format(module_src,module))
        else:
            print("Musisz podać nazwę modułu!")
    except ImportError as e:
        print(e)

class Shell(cmd.Cmd):
    def __init__(self):
        super().__init__()

    prompt = "#>"
    modules = []

    try:
        loader = ConfigManager("modules.yaml").loader
        for module_name in loader:
            modules.append(module_name)
    except ConfigManagerError as e:
        print(e)

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

#adres_user_password_sshport_remoteport
    def do_connect(self, arg):
        """Connecting via ssh"""
        conf_file, server_name = arg.split()
        try:
            conf = ConfigManager(conf_file)
            connection =  conf.show(server_name)["connection"]
            command = connection["adress"] + "_" + connection["user"]+ "_" + \
                    connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) 
            conn.send(command)
            t = None
            while t == None:
                t = conn.get_state()
            print(t)
        except Exception as e:
            print (e)
        
    def do_connectToList(self,arg):
        list_of_lists = arg.split(" ")
        for lista in list_of_lists:
            path = lista + ".yaml"
            try:
                self.connectToList(path)
            except ConfigManagerError as e:
                print (e)

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

    def connectToList(self, listFile):
        conf = ConfigManager(listFile)
        
        server_list = []
        for server in conf.loader:
            server_list.append(server)

        connection_list ={}
        for server in server_list:
            connection =  conf.show(server)["connection"]
            #Poprawić cmd
            # adres_user_password_sshport_remoteport
            command = connection["adress"] + "_" + connection["user"]+ "_" + \
                    connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"])

            conn.send(command)
            t = None
            while t == None:
              t = conn.get_state()
            #status_adres_localport
            server_status = t.split("_")
            connection_list[server_status[1]]=server_status[2]
            print("Connecting to" , connection["adress"], "[", server_status[0], "]")
        print(connection_list)

# if __name__ == '__main__':
try:
    Shell().cmdloop()
except KeyboardInterrupt:
    print("")
    pass