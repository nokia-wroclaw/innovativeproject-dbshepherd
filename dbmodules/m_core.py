import cmd
import re


class ParseArgsException(Exception):
    def __init__(self, msg):
        self.msg = msg

class ModuleCore(cmd.Cmd):
    def set_name(self, name):
        self.prompt = "[" + name + "]>"

    def parse_args(self, string="", n=0):
        list = re.findall('"+.*"+|[a-zA-Z0-9!@#$%^&*()_+-,./<>?]+', string)
        if len(list) == n or n == 0:
            r_list = []
            for l in list:
                r_list.append(l.replace('"', ''))
            return r_list
        else:
            raise ParseArgsException("Nieodpowiednia ilość argumentów")


    def do_exit(self, *args):
        return True

    def do_EOF(self, line):
        return True

    def emptyline(self):
        return False