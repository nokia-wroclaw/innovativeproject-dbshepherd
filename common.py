import connection
conn = None
try:
    conn = connection.Connection()
    conn.start()
    print("test")
except ConnectionRefusedError:
    print("Nie można połączyć się z ssh-shepherd, tunele będą tworzone lokalnie.")