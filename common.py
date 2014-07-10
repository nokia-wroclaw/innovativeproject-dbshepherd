import connection, os
conn = None
current_dir = '.'
app_dir = '.'

def init():
	app_dir = os.getcwd()
	current_dir = app_dir
	print('common init')

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
	app_dir = os.getcwd()
	os.chdir(app_dir)

def restore_cdir():
	os.chdir(app_dir)

try:
    conn = connection.Connection()
    conn.start()
except ConnectionRefusedError:
    print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")