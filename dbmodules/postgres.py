import sys

from prettytable import from_db_cursor

import m_core

sys.path.append("..")

import alias
import psycopg2

class Postgres(m_core.ModuleCore):
    def __init__(self,completekey='tab', stdin=None, stdout=None):
        super().__init__()
        self.set_name('Postgres')

    def do_query(self, args):
        try:
            v = self.parse_args(args, 3)
            values = v[0]
            print(v[1])
            #values = self.parse_args('conf.yaml testServer2.pgBase1 "SELECT * FROM shepherd2"', 3)

            try:
                ali = alias.Alias(values[0])
                adr = ali.show(values[1].split('.')[0])["connection"]["adress"]
                pwd = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["passwd"]
                usr = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["user"]
                db_name = ali.show(values[1].split('.')[0])[values[1].split('.')[1]]["name"]

                try:
                    conn = psycopg2.connect(dbname=db_name,user=usr,host=adr,password=pwd, port=1234)
                    cur = conn.cursor()
                    cur.execute(values[2])

                    pt = from_db_cursor(cur)
                    print(pt)

                except psycopg2.Error as e:
                    print('Error: ', e)
                except psycopg2.Warning as w:
                    print('Warning: ', w)
                except psycopg2.InterfaceError as e:
                    print('Error: ', e)
                except psycopg2.DatabaseError as e:
                    print('Error: ', e)

            except alias.AliasError as e:
                print(e)
            except Exception as e:
                print(e)


        except m_core.ParseArgsException as e:
            print(e)

