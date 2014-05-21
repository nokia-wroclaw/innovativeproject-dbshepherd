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
   
    def do_connect(self, arg):
        "Connect to (all), list, list.server"
        if arg == "":
            print ("connect to all...")
            import os
            for file in os.listdir("config"):
                if file.endswith(".yaml"):
                    list_name = file.title()[:file.rfind(".")]
                    print("connecting to...", list_name)
        else:   
            params = arg.split(".")
            if len(params) == 1:
                print ("connect list...")
                self.connectList("config/"+params[0]+".yaml")
            elif len(params) == 2:
                print ("connect serv...")
                try:
                    conf = ConfigManager("config/"+params[0]+".yaml")
                    connection =  conf.show(params[1])["connection"]
                    command = connection["adress"] + "_" + connection["user"]+ "_" + \
                            connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"])
                    try:
                        conn.send(command)
                        t = None
                        while t == None:
                            t = conn.get_state()
                        print(t)
                    except AttributeError as e:
                       print("CONNECTING USING LOCAL MANAGER!")
                except ConfigManagerError as e:
                    print (e)
                
                except Exception as e:
                    print (e)
            else:
                print ("error")

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

    def connectList(self, listFile):
        try:
            conf = ConfigManager(listFile)
        except Exception as e:
            print ("No conf file", listFile)
            return 1
        
        server_list = []
        for server in conf.loader:
            server_list.append(server)

        connection_list ={}
        for server in server_list:
            connection =  conf.show(server)["connection"]
            #Poprawić cmd
            # adres_user_password_sshport_remoteport
            command = connection["adress"] + "_" + connection["user"]+ "_" + \
                    connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) + "_no"
            try:
                conn.send(command)
                t = None
                while t == None:
                  t = conn.get_state()
                #status_adres_localport
                server_status = t.split("_")
                try:
                    connection_list[server_status[1]]=server_status[2]
                    print("Connecting to" , connection["adress"], "[", server_status[0], "]")
                except IndexError as e:
                    print(t)
            except AttributeError as e:
                print("CONNECTING USING LOCAL MANAGER!")
        print(connection_list)

# if __name__ == '__main__':
try:
    Shell().cmdloop()
except KeyboardInterrupt:
    print("")
    pass