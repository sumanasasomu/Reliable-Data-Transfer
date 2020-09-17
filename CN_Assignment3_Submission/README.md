Sender Side:

python3 senderApp.py <IP> <Port> <File to send> <Desired Output file name>
Example:
python3 senderApp.py 192.168.56.1 5001 abc.txt a

Receiver Side:

python3 receiverApp.py <Port>
Example:
python3 receiverApp.py 5001

Make sure that you enter the SAME Port Numbers while running both the files simultaneously.

After successful execution of both the files, the received file would be stored in the subfolder 'Storage/'

The files usesender.py and usereceiver.py are the source files used by the toy applications.

The file BadNet5.py has been taken from the internet, to emulate the losses, delays, corrupt packets, etc.
The file checkSum.py has been taken from the internet, to use a function that calculates check sum.
