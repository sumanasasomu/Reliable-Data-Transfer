from usesender import Sender
import sys

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])
sendFile_name = sys.argv[3]
sendFile_extension = sendFile_name.split('.')[-1]
storeFile_name = sys.argv[4]

# serverIP = input("Enter Server IP: ")
# serverPort = int(input("Enter Server Port: "))
# sendFile_name = input("Enter Input file name / relative path: ")
# sendFile_extension = sendFile_name.split('.')[-1]
# storeFile_name = input("Enter Output File Name (without extension): ")

s1 = Sender(serverIP,serverPort,sendFile_name,sendFile_extension, storeFile_name)
s1.run()