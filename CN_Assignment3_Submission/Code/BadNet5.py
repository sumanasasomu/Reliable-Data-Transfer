# FALL 2013 Computer Networks		SEECS NUST
# BESE 2
# Dr Nadeem Ahmed
# BadNet5:  a mix of drops, duplicates, errors and re-ordering of packets
# 5th dropped, 10th re-ordered, 15th duplicated, 20th errored.....
# Usage: BadNet.transmit instead of sendto


from socket import *
import time

class BadNet:

	dummy=' '
	reorder=0
	counter = 0
	error=1
	@staticmethod
	def transmit(csocket,message,serverName,serverPort):
#		print 'Got a packet' + str(BadNet.counter)
		
		if (BadNet.counter % 3) != 0:
			csocket.sendto(message,(serverName,serverPort))
			#print 'BadNet Sends properly packet No ' + str(BadNet.counter)
	
		else:

			if BadNet.error==1:
			#	print 'BadNet Dropped a packet No ' + str(BadNet.counter)
				BadNet.error=2				
				

			elif BadNet.error==2:
				if BadNet.reorder == 1:
			#		print 'BadNet re-ordering a packet No ' + str(BadNet.counter)
					csocket.sendto(message,(serverName,serverPort))
				# time.sleep(1)
					csocket.sendto(BadNet.dummy,(serverName,serverPort))
					BadNet.reorder=0
					BadNet.counter=BadNet.counter+1	
					BadNet.error=3
				else:
					BadNet.dummy=message
					BadNet.reorder=1
					BadNet.counter=BadNet.counter-1	



			elif BadNet.error==3:
			#	print 'BadNet Duplicated a packet No ' + str(BadNet.counter)
				csocket.sendto(message,(serverName,serverPort))

				csocket.sendto(message,(serverName,serverPort))
				# BadNet.error=4
				BadNet.error = 4


			elif BadNet.error==4:
			#	print 'BadNet creating packet errors packet No ' + str(BadNet.counter)
				
				print('CORRUPT ------')
				mylist=list(message)
#				get last char of the string
				# print('mylist type: ',type(mylist[-1]))		
				print(mylist)	
				x=(mylist[-1])
				# print('x type: ',type(x))
				if (x&1)==1:
					#if first bit set, unset it
					x &= ~(1)
				else:
					#if first bit not set, set it
					x |=  1
				
				# mylist[-1]=chr(x)
				# print('Hi badnet -- - ', mylist)

				dummy = bytes(mylist)
				# print(dummy)


				# print('badnet -------- join done')
				# print(dummy)
				# print(dummy.encode())

				csocket.sendto(dummy,(serverName,serverPort))
				BadNet.error=5

			elif BadNet.error == 5:
				print('************* Sleep Start **********', BadNet.counter)
				time.sleep(11)
				print('************* Sleep Stop **********', BadNet.counter)
				csocket.sendto(message,(serverName,serverPort))
				BadNet.error = 1

		BadNet.counter=BadNet.counter+1	
