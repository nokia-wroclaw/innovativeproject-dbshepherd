from ssh_cmd_manager import CmdManager
import time
try:
	c = CmdManager()
	c.start()
	while c.isAlive():
		time.sleep(1)

	print("Destroy!!!")
	
	try:
		c.server.close()
		c.permament_checker._stop()
		c._stop()
	except Exception as e:
		print (e)
	except:
		pass
		
except (KeyboardInterrupt, SystemExit):
	print ("kb int")
	try:
		c.server.close()
		c.permament_checker._stop()
		c._stop()
		
	except Exception as e:
		print (e)
	except:
		pass