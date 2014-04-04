from shutil import copyfile

import m_core


class Test_Mod(m_core.ModuleCore):
    def __init__(self,completekey='tab', stdin=None, stdout=None):
        super().__init__()
        self.set_name('Test_mod')

    def do_exit(self,*args):
        return True

    def do_hello(self, t):
        print('Hello')

    def do_copy(self, a=""):
        """Copy file, use:
        copy <from> <to>"""
        m = (a.split(' '))
        print(m.size())
        copyfile(*(a.split(' ')))

    def do_EOF(self, line):
        return True

    def emptyline(self):
        return False
