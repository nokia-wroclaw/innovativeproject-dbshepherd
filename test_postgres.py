import os
import unittest
from mod_postgres import Postgres

test1_dump_file = "test1_dump"

class PostgresTest(unittest.TestCase):

	def test1_dump(self):
		#if exists remove test1_dump* file
		for file in os.listdir("dump"):
					if file.startswith("test1_dump"):
						if os.path.exists("dump/" + file.title()):
							os.remove("dump/" + file.title())
		
		pg = Postgres()
		test = pg.do_dump("lista_test.ShouldBeOK.pgBase_test " + test1_dump_file)
		#test if file exists
		counter = 0
		for file in os.listdir("dump"):
					if file.startswith("test1_dump"):
						counter += 1
						if os.path.exists("dump/" + file.title()):
							os.remove("dump/" + file.title())
		self.assertNotEqual(counter,0)
	
if __name__ == '__main__':
	unittest.main(verbosity=2)#