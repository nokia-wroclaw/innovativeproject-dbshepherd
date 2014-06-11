from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from getpass import getpass


import yaml
#Przykładowy yaml
aes_yaml = """
 alias:
   haslo: cosinnego
 alias2:
   haslo: passwd
"""

def encrypt(string):
	#init
	rndfile = Random.new()

	#read file####
	to_enc = string.encode("UTF-8")
	#.############
	encready = b''

	ctr = 0

	block = to_enc[ctr:ctr+16]
	if len(block) < 16:
		encready +=  block
	while len(block) == 16:
		block = to_enc[ctr:ctr+16]
		encready +=  block
		ctr += 16

	padding = 16 - len(block)
	rnd = rndfile.read(padding)
	encready += rnd
	
	passwd = getpass("Input password: ")
	hash = SHA256.new()

	hash.update(passwd.encode("UTF-8"))
	key = hash.digest()
	rnd =  rndfile.read(16)
	obj = AES.new(key, AES.MODE_CBC, rnd)
	to_save = obj.encrypt(encready)
	#write file####
	return to_save, padding, rnd
	#.############
	
def decrypt(string, padding, IV):
	passwd = getpass("Input password: ")
	hash = SHA256.new()
	hash.update(passwd.encode("UTF-8"))
	key = hash.digest()
	obj2 = AES.new(key, AES.MODE_CBC, rnd)
	decrypted = obj2.decrypt(string)
	return decrypted[:len(decrypted)-padding]

	#docelowo tylko to importujemy

#Szyfrujemy yamla
ciphertext, padding, rnd = encrypt(aes_yaml)


print("Ok, zaszyfrowaliśmy to teraz wyciągnijmy hasło")
alias_to_get = input("Hasło do jakiego aliasu chcesz? ")
print("Decrypting...")
try:
	#odczytujemy z pliku itd.
	decrypted = decrypt(ciphertext,padding,rnd).decode()
	loader = yaml.load(decrypted)
	try:
		print(loader[alias_to_get]["haslo"])
	except KeyError:
		print("Brak aliasu", alias_to_get)
except Exception as e:
	print(e)



