from checkSum import myCheckSum
from socket import *
import sys
import math
import time
import pickle
from pathlib import Path
import signal
import os
# from BadNet5 import *


CONNECT_TIMEOUT = 20
INTITIAL_TIMEOUT = 3
SOCKET_TIMEOUT = 2

class executionDetails:

	def __init__(self):
		self.time = 0
		self.success = False
		# self.ipFname = "input.txt"
		self.opFname = "output.txt"
		self.fileSize = 0
		self.numOfPackets = 0
		self.message = "FAILED"
		self.start = 0
		self.end = 0

	def getTime(self):
		return self.time
	def getStart(self):
		return self.start
	def getEnd(self):
		return self.end
	def getSuccess(self):
		return self.success
	# def getIpFname(self):
	# 	return self.ipFname
	def getOpFname(self):
		return self.opFname
	def getFileSize(self):
		return self.fileSize
	def getNumOfPackets(self):
		return self.numOfPackets
	def getMessage(self):
		return self.message

	def setTime(self):
		self.time = self.end - self.start
	def setStart(self, sstart):
		self.start = sstart		
	def setEnd(self, sEnd):
		self.end = sEnd		
	def setSuccess(self, ssuccess):
		self.success = ssuccess
	# def setIpFname(self,sipFname):
	# 	self.ipFname = sipFname
	def setOpFname(self, sopFname):
		self.opFname = sopFname
	def setFileSize(self, ssendFile_size):
		self.fileSize = ssendFile_size
	def setNumOfPackets(self, snum_packets):
		self.numOfPackets = snum_packets
	def setMessage(self, smessage):
		self.message = smessage


class Receiver():

	serverSocket = None
	isSuccess = False
	no_of_packets = 0
	transfer_time = 0
	received_file_size = 0

	def __init__(self,serverPort):
		self.serverPort=serverPort
		self.op_filename="output.txt"

		# asdas
	def signal_handler(self, signal, frame):
		try:
			print('\nCtrl+C => STOP')
			self.serverSocket.close()
			sys.exit()
		except:
			# serverSocket.close()
			sys.exit()


	def startReceiving(self, fileTransferStatus):

		message_packet = []
		TIMEOUT = INTITIAL_TIMEOUT
		packets_received_so_far = 0
		packets_to_be_acked = 0
		last_any_packet_time = time.time()	
		sender_inactivity_timout = CONNECT_TIMEOUT

		fileTransferStarted = False
		SUCCESS = False # only till receiving last packet. Don't know if acknowledged.
		SENDER_DOWN = False

		timer_for_FIN = False

		seqNo = 0
		expected_seqNo = 0

		canSendSynAck = 0 # 1 = need to send; 2 = sent and 3 = sent and reached
		ack_list = []
		f = "file reader"
		RTT=[]
		itr=0
		starttime_flag=False
		try:
			while(True):
				try:

					if(time.time() - last_any_packet_time > sender_inactivity_timout and fileTransferStarted == True):
						if(SUCCESS == True and fileTransferStatus.getSuccess() == True):
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('File Transfer Successful')
							break
						elif(SUCCESS == True and fileTransferStatus.getSuccess() == False):
							print('inactive but got the file. dont know if receiver knows that')
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('Received File but sender might have gone down before receiving ACK for nth Packet')
							break							
						else:
							fileTransferStatus.setMessage("Sender Down. Detected atleast"+ str(sender_inactivity_timout) + " seconds Inactivity")
							SENDER_DOWN == True
							break

					message_packet_str, clientAddress = self.serverSocket.recvfrom(2048)
					fileTransferStarted = True
					if(itr==0):
						self.serverSocket.settimeout(SOCKET_TIMEOUT)

					
					
						

					if(itr>0):
						prev_packet_time = last_any_packet_time 
						last_any_packet_time = time.time()
						RTT.append(last_any_packet_time - prev_packet_time)
						# print('This RTT was: ', RTT[-1])
					else:
						last_any_packet_time = time.time()

					message_packet = list(pickle.loads(message_packet_str))
					checkSum = message_packet[0]
					seqNo = message_packet[1]
					message = message_packet[2]

					calc_checkSum = str(myCheckSum(str(message) + "" + str(seqNo)))

					if(calc_checkSum != 'False' and calc_checkSum == checkSum and seqNo == expected_seqNo):
						
						expected_seqNo += 1
						ack_checkSum = str(myCheckSum(str(expected_seqNo)))
						ack_packet = [ack_checkSum, expected_seqNo]

						if(expected_seqNo == packets_to_be_acked + 1 and expected_seqNo > 1):
							canSendSynAck = 3 # sent and reached
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('File Transfer Successful')								
							break


						if(canSendSynAck == 1 and expected_seqNo == packets_to_be_acked):
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('File Transfer Successful')
							print('sent SYN-ACK, received '+str(seqNo)+" sent val "+str(expected_seqNo))
							canSendSynAck = 2 # meaning sent

						self.serverSocket.sendto(pickle.dumps(ack_packet), clientAddress)
						# BadNet.transmit(self.serverSocket, pickle.dumps(ack_packet), clientAddress[0], int(clientAddress[1]))


						ack_list.append(ack_packet) 
						print('Received Expected Packet - ACKed ' + str(seqNo) + ' with ACK = ' + str(expected_seqNo))
						packets_received_so_far += 1
						
						if(seqNo == 0):

							# Start Transfer Timer
							if(starttime_flag==False):
								fileTransferStatus.setStart(time.time())
								starttime_flag=True

							data_details = message.split(';')
							packets_to_be_acked = int(data_details[0])
							file_format = str(data_details[1])
							opname = str(data_details[2])
							
							# UPDATE TOTAL EXPECTED PACKETS
							print('Packets expected to be received', packets_to_be_acked)							
							fileTransferStatus.setNumOfPackets(packets_to_be_acked)


							# CREATE FILE TO STORE DATA
							oppath = "./Storage/"+ opname
							print('OPPATH',oppath)
							looppath = oppath + '.' + file_format
							origpath = oppath
							counter = 1
							while(True):
								if Path(looppath).is_file():
									if(counter == 1):
										print('File name already exists. Renaming it.')
									looppath = origpath + "_" + str(counter) + "." + file_format
									counter +=1
								else:
									oppath = looppath
									break
							fileTransferStatus.setOpFname(oppath)
							# FILE READY

							f = open(oppath, "wb")
							self.serverSocket.settimeout(SOCKET_TIMEOUT) #seconds


						# IF 1 to n packets are receoved, write them to the file
						elif(seqNo >= 1 and seqNo <= packets_to_be_acked-2):
							f.write(message)	
							if(seqNo == packets_to_be_acked-2):
								SUCCESS = True
								fileTransferStatus.setEnd(time.time())
								fileTransferStatus.setTime()
								f.close()
								file_size_bytes = os.path.getsize(oppath)
								fileTransferStatus.setFileSize(file_size_bytes)

						# IF seqNo = n+1 it is a SYN Packet. Can send SYN ACK should send n+2 in ACK packet
						# The sender had received the last ACK for nth data packet. So it is successful.
						elif(seqNo == packets_to_be_acked-1):
							canSendSynAck = 1


						elif(seqNo == packets_to_be_acked):
							break
							# pass

					else:
						if(starttime_flag==False):
								fileTransferStatus.setStart(time.time())
								starttime_flag=True
						print('Received ' + str(seqNo) + ' Expected packet ' + str(expected_seqNo))
						if(len(ack_list) > 0):
							ack_packet = ack_list[-1]
							prev_ack_val = ack_packet[1]
							# BadNet.transmit(self.serverSocket, pickle.dumps(ack_packet), clientAddress[0], int(clientAddress[1]))					
							self.serverSocket.sendto(pickle.dumps(ack_packet), clientAddress)
							print('Re-ACKed ' + str(seqNo) + ' with ACK = ' + str(prev_ack_val))

				except timeout:
					print('Socket time out', TIMEOUT)
					print('diff ',time.time() - last_any_packet_time)
					print('sender ', sender_inactivity_timout)
					print('fileTransferStarted ',fileTransferStarted)
					if(time.time() - last_any_packet_time > sender_inactivity_timout and fileTransferStarted == True):
						if(SUCCESS == True and fileTransferStatus.getSuccess() == True):
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('File Transfer Successful')
							break
						elif(SUCCESS == True and fileTransferStatus.getSuccess() == False):
							print('inactive but got the file. dont know if receiver knows that')
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('Received File but sender might have gone down before receiving ACK for nth Packet')
							break							
						else:
							fileTransferStatus.setMessage("Sender Down. Detected atleast"+ str(sender_inactivity_timout) + " seconds Inactivity")
							SENDER_DOWN == True
							break

					if(time.time() - last_any_packet_time > TIMEOUT):

						if(itr>0):
							TIMEOUT = sum(RTT)/len(RTT)

						# If ACK packet is dropped re-ack them
						prev_ack_val = 0
						if(len(ack_list) > 0):
							ack_packet = ack_list[-1]
							prev_ack_val = ack_packet[1]
							self.serverSocket.sendto(pickle.dumps(ack_packet), clientAddress)
							# BadNet.transmit(self.serverSocket, pickle.dumps(ack_packet), clientAddress[0], int(clientAddress[1]))					
							print('Re-ACKed with ACK = ' + str(prev_ack_val))

						# if SYN-ACK sent but reached OR sent and reached. In ny case, Terminate

						# only sent then wait for one more timeout
						if(canSendSynAck == 2):
							if(timer_for_FIN == False):
								timer_for_FIN = True
							else:
								fileTransferStatus.setSuccess(True)
								fileTransferStatus.setMessage('File Transfer Successful')								
								break
						
						# sent and reached then terminate immediately
						if(canSendSynAck == 3):
							fileTransferStatus.setSuccess(True)
							fileTransferStatus.setMessage('File Transfer Successful')								
							break						


				except OSError:
					print("Oops!", sys.exc_info(), "occured.")				
					sys.exit()
				
				except SystemExit:
					print("Oops!", sys.exc_info(), "occured.")	
					sys.exit()

				except:
					print("Oops!", sys.exc_info(), "occured.")

				itr+=1


			# While loop Ended		


		except SystemExit:
			print("Oops!", sys.exc_info(), "occured.")	
			sys.exit()

		except:
			print("Oops!", sys.exc_info(), "occured.")
		
		# print('isSuccess', self.isSuccess)
		# print('no_of_packets', self.no_of_packets)
		# print('transfer_time', self.transfer_time)
		# print('received_file_size', self.received_file_size)

	def run(self):

		signal.signal(signal.SIGINT, self.signal_handler)

		# 1. EXECUTION STATUS MANAGEMENT
		self.fileTransferStatus = executionDetails()


		print('I am UP!')

		self.serverSocket = socket(AF_INET, SOCK_DGRAM)
		# print('socket created')

		self.serverSocket.bind(('',self.serverPort))
		print('Listening....')

		self.startReceiving(self.fileTransferStatus)
		self.serverSocket.close()


		print(self.fileTransferStatus.getMessage())

		if(self.fileTransferStatus.getSuccess() == True):
			print('Your file is stored at:',self.fileTransferStatus.getOpFname())
			print('File Size Received in Bytes:', self.fileTransferStatus.getFileSize())
			print('Number of Packets:',self.fileTransferStatus.getNumOfPackets())
			print('Transfer Time in seconds:',self.fileTransferStatus.getTime())
			print('Throughput in bytes per second: ', (self.fileTransferStatus.getFileSize()/self.fileTransferStatus.getTime()))
			print('Throughput in bits per second: ', 8*(self.fileTransferStatus.getFileSize()/self.fileTransferStatus.getTime()))



# fileTransferStatus.setMessage("Couldn't Reach Receiver. Detected "+ str(server_contact_timeout) + " seconds Inactivity")						
# fileTransferStatus.setIpFname()
# fileTransferStatus.setOpFname()
# fileTransferStatus.setSuccess(True)
# fileTransferStatus.setEnd(time.time())
# fileTransferStatus.setTime()
# fileTransferStatus.setMessage('File Transfer Successful')
# fileTransferStatus.setStart(time.time())


# self.fileTransferStatus.setMessage("Couldn't Reach Receiver. Detected "+ str(server_contact_timeout) + " seconds Inactivity")						
# self.fileTransferStatus.setIpFname()
# self.fileTransferStatus.setOpFname()
# self.fileTransferStatus.setSuccess(True)
# self.fileTransferStatus.setEnd(time.time())
# self.fileTransferStatus.setTime()
# self.fileTransferStatus.setMessage('File Transfer Successful')
# self.fileTransferStatus.setStart(time.time())

# if(seqNo == packets_to_be_acked-2):
# 	print('Received All Data Packets')
# 	fileTransferStatus.setSuccess(True)
# 	fileTransferStatus.setEnd(time.time())
# 	fileTransferStatus.setTime()
# 	fileTransferStatus.setMessage('File Transfer Successful')							
# 	packets_received_so_far += 1

# 	fileTransferStatus.setSuccess(True)
# 	fileTransferStatus.setMessage('File Transfer Successful')