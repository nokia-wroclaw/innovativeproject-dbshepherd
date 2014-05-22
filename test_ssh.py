import unittest
from ssh_tunnelmanager import TunnelManager
import common

conn = common.conn
manager = TunnelManager()

cmd = "antivps.pl_dbshepherd_dbshepherd_22_5432_no"
common.conn.send(cmd)
ans = None
while ans == None:
    ans = common.conn.get_state()
print(ans)


class SShTest(unittest.TestCase):
    def test_connect_no_permament(self):
        cmd = "antivps.pl_dbshepherd_dbshepherd_22_5432_no"
        common.conn.send(cmd)
        ans = None
        while ans == None:
            ans = common.conn.get_state()
        answers = ans.split("_")
        self.assertEqual("ok", answers[0])
        self.assertEqual("antivps.pl", answers[1])

if __name__ == '__main__':
    unittest.main()