from dbmodules import m_core

import sys
sys.path.append("..")

import alias
import psycopg2

class Postgres(m_core.ModuleCore):
    def __init__(self,completekey='tab', stdin=None, stdout=None):
        super().__init__()
        self.set_name('Postgres')

    def do_query(self, args):
        values = args.split(' ')
        ali = alias.Alias(values[0])
        adr = ali.show(values[1].split('.')[0])["connection"]["adress"]
        usr = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["user"]
        pwd = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["passwd"]
        db_name = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["name"]

        try:
            conn = psycopg2.connect(dbname=db_name,user=usr,host=adr,password=pwd, port=1234)
            cur = conn.cursor()
            cur.execute(values[2])
            rows = cur.fetchall()

            for row in rows:
                for cell in row:
                    print(cell, "   ", end='')
                print("\n");
        except:
            print("Problem z połączeniem!")