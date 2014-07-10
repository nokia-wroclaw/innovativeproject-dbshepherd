import connection, os

conn = None
keepass_path = None
dump_path = None
config_path = None

current_dir = '.'
app_dir = '.'

def init():
	app_dir = os.getcwd()
	current_dir = app_dir

def get_cdir():
	return current_dir

def chdir(dir):
	global current_dir
	tmp = os.getcwd()
	os.chdir(current_dir)
	os.chdir(dir)
	current_dir = os.getcwd()
	os.chdir(tmp)

def set_cdir_and_store():
	global app_dir
	app_dir = os.getcwd()
	os.chdir(current_dir)

def restore_cdir():
	global app_dir
	os.chdir(app_dir)

try:
    conn = connection.Connection()
    conn.start()
except ConnectionRefusedError:
    print("Unable to connect to ssh-shepherd. Db-shepherd might not work properly.")