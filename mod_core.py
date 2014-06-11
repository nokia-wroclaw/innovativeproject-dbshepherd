import cmd
import re


class ParseArgsException(Exception):
	def __init__(self, msg):
		self.msg = msg

class ModuleCore(cmd.Cmd):
	def set_name(self, name):
		self.prompt = "[" + name + "]>"

	def parse_args(self, string="", n=0, m=0):
		list = re.findall('"+.*"+|[a-zA-Z0-9!@#$%^&*()_+-,./<>?]+', string)
		arg_counter = len(list);
		if (arg_counter >= n and arg_counter <= m) or (arg_counter == n and m == 0) or n == 0:
			r_list = []
			for l in list:
				r_list.append(l.replace('"', ''))
			return (r_list, len(list))
		else:
			raise ParseArgsException("Nieodpowiednia ilość argumentów")

	def do_warn(self, args):
		try:
			(values, values_num) = self.parse_args(args, 0, 1)
			if values_num == 1:
				if values[0] == 'on':
					print('Warnings on')
					self.warn = True
				elif values[0] == 'off':
					print('Warnings off')
					self.warn = False
				else:
					print('Incorrect argument.')
			else:
				if self.warn == True:
					print('Status: on')
				else:
					print('Status: off')

		except ParseArgsException as e:
			print(e)


	def do_exit(self, *args):
		return True

	def do_EOF(self, line):
		return True

	def emptyline(self):
		return False