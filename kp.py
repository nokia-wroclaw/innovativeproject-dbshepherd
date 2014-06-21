from keepass import kpdb

class KeePassError(Exception):
	def __init__(self, value):
		self.value = value

def get_password(file, masterpass, alias):
	db = kpdb.Database(file, masterpass)
	ret = ""
	print(db)
	for entry in db.entries:
		if alias == entry.username:
			ret = entry.password
	if ret == "":
		raise KeePassError(alias + " not present in db")
	else:
		return ret
		
			
get_password ("keys.kdb", "nsnqwerty", "dbshepherd")