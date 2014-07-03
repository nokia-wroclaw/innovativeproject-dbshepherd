import sys, os, platform

if sys.platform == 'linux':
	print('Installing under linux')
	os.system("python3 setup.py install")
elif sys.platform == 'win32':
	print('Installing under Windows')
	#binarki pycrypto, psycopg2
	bits = platform.architecture()[0]
	print (bits)
	if bits == '64bit':
		bit_suffix = 'x64'
	else:
		bit_suffix = 'x32'
	run = "pycrypto-" + bit_suffix + ".exe"
	os.system(run)
	run = "psycopg2-" + bit_suffix + ".exe"
	os.system(run)
	run = "pyreadline-" + bit_suffix + ".exe"
	os.system(run)
	#ez_install
	os.system("python setup.py install")
else:
	print("System not supported try to run setup.py")