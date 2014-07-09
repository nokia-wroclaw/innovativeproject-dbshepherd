import connection
conn = None
current_dir = ''

def get_cdir():
	return current_dir

try:
    conn = connection.Connection()
    conn.start()
except ConnectionRefusedError:
    print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")