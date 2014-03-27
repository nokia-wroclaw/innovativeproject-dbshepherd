import cmd

class ModuleCore(cmd.Cmd):
    def set_name(self, name):
        self.prompt = "[" + name + "]>"

    def do_exit(self,*args):
        return True

    def do_EOF(self, line):
        return True

    def emptyline(self):
        return False