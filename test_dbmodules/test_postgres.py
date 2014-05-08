import unittest
import sys
sys.path.append("..")
from dbmodules.postgres import Postgres


class PostgresTest(unittest.TestCase):
    pgr = Postgres();
    pgr.do_raw_query('test.yaml test.test "DROP TABLE if exists test_table;"')
    pgr.do_raw_query('test.yaml test.test "CREATE TABLE test_table(a int, b int, c varchar(20));"')

    def test_insert(self):
        self.pgr.do_raw_query('test.yaml test.test "INSERT INTO test_table VALUES(1, 2, \'x\');"')
        self.pgr.do_raw_query('test.yaml test.test "INSERT INTO test_table VALUES(3, 4, \'v\');"')
        test = self.pgr.do_raw_query('test.yaml test.test "SELECT * FROM test_table;"')

        self.assertEqual(test[0][0], 1)
        self.assertEqual(test[0][1], 2)
        self.assertEqual(test[0][2], 'x')

        self.assertEqual(test[1][0], 3)
        self.assertEqual(test[1][1], 4)
        self.assertEqual(test[1][2], 'v')

        self.pgr.do_raw_query('test.yaml test.test "DROP TABLE IF EXISTS test_table;"')

if __name__ == '__main__':
    unittest.main()