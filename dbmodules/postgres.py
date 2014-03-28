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
        try:
            values = self.parse_args(args, 3)
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
                    columns = [desc[0] for desc in cur.description]

                    rows = cur.fetchall();

                    print()

                    print('+', end='')
                    for column in columns:
                        for i in range(0, len(column.ljust(15, ' '))):
                            print("-", end='')
                        print('+', end='')
                    print()

                    print('|', end='')
                    for column in columns:
                        print(column.ljust(15, ' '), end='')
                        print('|', end='')

                    print('\n|', end='')
                    for column in columns:
                        for i in range(0, len(column.ljust(15, ' '))):
                            print("-", end='')
                        print('|', end='')
                    print()

                    for row in rows:
                        for cell in row:
                            print('|', end='')
                            print(str(cell).ljust(15, ' '), end='')
                        print('|', end='')
                        print()

                    print('+', end='')
                    for column in columns:
                        for i in range(0, len(column.ljust(15, ' '))):
                            print("-", end='')
                        print('+', end='')
                    print()


                    print()

                except psycopg2.Error as e:
                    print(e)
                except psycopg2.Warning as w:
                    print(w)

            except alias.AliasError as e:
                print(e)
            except Exception as e:
                print(e)


        except m_core.ParseArgsException as e:
            print(e)

