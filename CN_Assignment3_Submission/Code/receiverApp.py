from usereceiver import Receiver
import sys
import os

if not os.path.exists('Storage'):
	os.makedirs('Storage')

#take inputs


serverPort = int(sys.argv[1])


# serverPort = int(input("Enter Port number: "))


r1 = Receiver(serverPort)
r1.run()