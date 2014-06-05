import connection
conn = None

try:
    conn = connection.Connection()
    conn.start()
except ConnectionRefusedError:
    print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")