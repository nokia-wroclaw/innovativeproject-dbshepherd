import sys

from prettytable import from_db_cursor

import m_core

sys.path.append("..")

import configmanager
import psycopg2

class Postgres(m_core.ModuleCore):
    def __init__(self,completekey='tab', stdin=None, stdout=None):
        super().__init__()
        self.set_name('Postgres')

    def do_query(self, args):
        try:
            (values,X) = self.parse_args(args, 3)
            [server_name, base_name] = values[1].split('.')
            file_name = values[0]

            try:
                conf = configmanager.ConfigManager(file_name).show(server_name)
                adr = conf["connection"]["adress"]
                pwd = conf[base_name]["passwd"]
                usr = conf[base_name]["user"]
                db_name = conf[base_name]["name"]

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

            except configmanager.ConfigManagerError as e:
                print(e)
            except Exception as e:
                print(e)


        except m_core.ParseArgsException as e:
            print(e)
        except Exception as e:
            print(e)

