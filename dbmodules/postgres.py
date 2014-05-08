import copy
from prettytable import from_db_cursor
import sys
import m_core

sys.path.append("..")
import common
sshshepherd_connection = common.conn

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
                connection = conf["connection"]
                if connection["type"] == "ssh":
                    command = connection["adress"] + "_" + connection["user"]+ "_" + \
                        connection["passwd"] + "_" + str(connection["sshport"])  + "_" + str(connection["remoteport"]) 
                    sshshepherd_connection.send(command)
                    odp = None
                    while odp == None:
                        odp = sshshepherd_connection.get_state()
                    status, hostname, db_port = odp.split("_")
                    adr = "localhost"
                else:
                    adr = connection["adress"]
                    db_port = connection["remoteport"]

                pwd = conf[base_name]["passwd"]
                usr = conf[base_name]["user"]
                db_name = conf[base_name]["name"]

                try:
                    pg_conn = psycopg2.connect(dbname=db_name,user=usr,host=adr,password=pwd, port=db_port)
                    cur = pg_conn.cursor()
                    cur.execute(values[2])

                    pt = from_db_cursor(cur)
                    if(pt != None):
                        print(pt)
                    pg_conn.commit()

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
            # except Exception as e:
            #     print(e)

        except configmanager.ConfigManagerError as e:
            print(e)
        # except m_core.ParseArgsException as e:
        #     print(e)
        # except Exception as e:
        #     print(e)
    def do_raw_query(self, args):
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
                    conn = psycopg2.connect(dbname=db_name,user=usr,host=adr,password=pwd, port=5432)
                    cur = conn.cursor()
                    cur.execute(values[2])
                    conn.commit()

                    return cur.fetchall();

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
