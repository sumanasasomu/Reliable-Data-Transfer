from checkSum import myCheckSum
from socket import * 
import math
import threading
from threading import Semaphore,BoundedSemaphore
import time
import sys
import struct
import pickle
import signal
import os
# from BadNet5 import *

CONNECT_TIMEOUT = 20
CHUNK_SIZE = 100
INITIAL_TIMEOUT = 3
SOCKET_TIMEOUT = 2

class executionDetails:
 
	def __init__(self):
		self.time = 0
		self.success = False
		self.ipFname = "input.txt"
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
	def getIpFname(self):
		return self.ipFname
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
	def setIpFname(self,sipFname):
		self.ipFname = sipFname
	def setOpFname(self, sopFname):
		self.opFname = sopFname
	def setFileSize(self, ssendFile_size):
		self.fileSize = ssendFile_size
	def setNumOfPackets(self, snum_packets):
		self.numOfPackets = snum_packets
	def setMessage(self, smessage):
		self.message = smessage


# python3 senderApp.py 192.168.29.2 5001 input2.txt oup_fname

class ClientClassThread(threading.Thread):

	# THREAD 1 and 2
	sender_windowBase = 1
	sender_windowSize = 8
	sender_window = []

	# THREAD 1
	seqNo = 0
	
	# THREAD 2
	itr = 0
	# highest_ack_so_far = 0
	last_any_ack_time = time.time()
	last_valid_ack_time = time.time()
	valid_ack_count = 0
	any_ack_count = 0
	atleast_one_ack_received = False
	ack_val = 0
	window_slide_time = time.time()

	# Exception Block
	socket_timeout_counter = 0
	packets_rec_after_timer = 0
	server_contact_timeout = CONNECT_TIMEOUT #SERVER CONNECTIVITY TIMEOUT
	server_contact_start = time.time()

	RTT = []
######################################################################################################
 

	# CONSTRUCTOR
	def __init__(self, threadID, TIMEOUT, pool_sema, db, clientSocket, fileTransferStatus):
		# invoke super class constructor
		threading.Thread.__init__(self)
		# assign thread ID
		self.threadID = threadID    
		self.TIMEOUT = TIMEOUT
		self.pool_sema = pool_sema
		self.rec_down = False
		self.db = db
		self.clientSocket = clientSocket
		self.fileTransferStatus = fileTransferStatus
		self.SYNrequest = 0
		self.FINrequest = 0
		self.expected_ACK = 0
		self.waitingToClose = False

	def setNeighbours(self,neigh):  
		self.neighbour = neigh
 
 
	def stop(self):
		self.__stop = True
 
 
	# implement run from Thread class
	def run(self):
 
		# HANDLE DATA PACKETS
		if(self.threadID == 1):
 
			n = self.db.segments_count
			while(self.rec_down == False):
				try:
					if(self.rec_down == False and self.seqNo <= self.db.segments_count):
							message = ""
							if(self.seqNo == 0):
								message = str(self.db.segments_count+2)+";"+str(self.db.sendFile_extension)+";"+str(self.db.storeFile_name)

							else:
								message = (self.db.message_segments[self.seqNo-1])
	 
							checkSum = str(myCheckSum(str(message) + "" + str(self.seqNo)))
							message_packet = [checkSum, self.seqNo, message]
	 
							if(self.rec_down == True):
								break

							# while(len(ClientClassThread.sender_window) >= ClientClassThread.sender_windowSize and self.rec_down == False):
							#   pass

							if(len(ClientClassThread.sender_window) < ClientClassThread.sender_windowSize):
								# self.pool_sema.acquire()
								ClientClassThread.sender_window.append(message_packet)
								# self.pool_sema.release()
								
								# BadNet.transmit(self.clientSocket, pickle.dumps(message_packet), self.db.serverIP, self.db.serverPort)
								self.clientSocket.sendto(pickle.dumps(message_packet),(self.db.serverIP, self.db.serverPort))
								
								if(self.seqNo == 0):
									self.fileTransferStatus.setStart(time.time())
	 
								print('Sent Data Packet =', self.seqNo)
								
								self.seqNo += 1
 
					elif(self.SYNrequest == 1 and (self.seqNo == n+1)):
						# send this packet exclusively
						for i in range(len(ClientClassThread.sender_window)):
							del ClientClassThread.sender_window[0]
						
					#if server asks for the SYN packet it means it had received all the data packets
						
						# not really req here. Anyways we are updating it while setting SYNrequest to 1.
						if(self.fileTransferStatus.getSuccess() != True):
							self.fileTransferStatus.setSuccess(True)
							self.fileTransferStatus.setMessage('File Transfer Successful')
							print('Marked Successful')
						
						message = "SYN"
						checkSum = str(myCheckSum(str(message) + "" + str(self.seqNo)))
						message_packet = [checkSum, self.seqNo, message]

						# BadNet.transmit(self.clientSocket, pickle.dumps(message_packet), self.db.serverIP, self.db.serverPort)
						self.clientSocket.sendto(pickle.dumps(message_packet),(self.db.serverIP, self.db.serverPort))
						ClientClassThread.sender_window.append(message_packet)
						self.seqNo += 1 #becomes n+2

						self.SYNrequest = 2 #meaning on receiving request, sent SYN to window
						self.expected_ACK = n+2

					elif(self.FINrequest == 1 and self.seqNo == n+2):
						for i in range(len(ClientClassThread.sender_window)):
							del ClientClassThread.sender_window[0]
						
						message = "FIN"
						checkSum = str(myCheckSum(str(message) + "" + str(self.seqNo)))
						message_packet = [checkSum, self.seqNo, message]

						# BadNet.transmit(self.clientSocket, pickle.dumps(message_packet), self.db.serverIP, self.db.serverPort)
						self.clientSocket.sendto(pickle.dumps(message_packet),(self.db.serverIP, self.db.serverPort))
						ClientClassThread.sender_window.append(message_packet)
						self.seqNo += 1 #here it becomes n+3                                                        
						self.FINrequest = 2 #meaning on receiving request, sent FIN to window

						self.SYNrequest = 3 # meaning SYN sent and reached
						self.expected_ACK = n+3


				except OSError:
					print("Oops!", sys.exc_info()[0], "occured.")                   
					sys.exit()
				
				except SystemExit:
					print("Oops!", sys.exc_info()[0], "occured.")   
					sys.exit()

				except:
					print("1. Oops!", sys.exc_info(), "occured.")
					sys.exit()


		# HANDLE ACKS               
		elif (self.threadID == 2):

			self.last_any_ack_time = time.time() #time when the last ack was received
			# self.last_valid_ack_time = time.time()          

			while(self.rec_down == False):
				try:
					ack_packet_string, serverAddress = self.clientSocket.recvfrom(2048)
					self.any_ack_count += 1
					self.packets_rec_after_timer += 1 #Will be set to sero once timer starts but not used anywhere so far

					if(self.itr > 0):
						prev_any_ack_time = self.last_any_ack_time
						self.last_any_ack_time = time.time()
						self.RTT.append(self.last_any_ack_time - prev_any_ack_time)
					else:
						last_any_ack_time = time.time()

					ack_packet = []
					# print('pickle1')
					# print(ack_packet_string)
					ack_packet = pickle.loads(ack_packet_string)
					ack_checkSum = ack_packet[0]
					self.ack_val = ack_packet[1]

					del ack_packet

					# calculate checksum
					calc_ack_checkSum = str(myCheckSum(str(self.ack_val)))
					
					if(calc_ack_checkSum != 'False' and calc_ack_checkSum == ack_checkSum):
						
						# if requesting data packets packet
						if(self.ack_val <= self.db.segments_count):
							self.atleast_one_ack_received = True
							# self.highest_ack_so_far = self.ack_val
							self.valid_ack_count += 1
							print('--ACK Received = ',self.ack_val)
							# slide to the last highest ack received.
							
	 						
							while(ClientClassThread.sender_windowBase < self.ack_val and len(ClientClassThread.sender_window) > 0):
								# self.pool_sema.acquire()
								self.window_slide_time = time.time()
								ClientClassThread.sender_windowBase += 1
								del ClientClassThread.sender_window[0]
								# self.pool_sema.release()
		 
						# if requesting SYN packet. if ACK = n+1
						elif(self.ack_val == self.db.segments_count+1):
							print('--ACK Received Requesting SYN = ',self.ack_val)

							# set SUCCESS
							self.fileTransferStatus.setSuccess(True)
							self.fileTransferStatus.setEnd(time.time())
							self.fileTransferStatus.setTime()

							self.neighbour.SYNrequest = 1
							self.SYNrequest = 1

						# if requesting FIN packet. ACK = n+2; Means received SYN succesfully
						elif(self.ack_val == self.db.segments_count+2):
							print('--ACK Received requesting FIN. Means SYN reached succesfully = ', self.ack_val)
							self.neighbour.FINrequest = 1
							self.FINrequest = 1

						# if requesting Out of limit packet. ACK = n+3; Means received FIN succesfully
						elif(self.ack_val == self.db.segments_count+3):
							self.SYNrequest = 3 #sent and reached
							self.FINrequest = 3 #sent and reached
							self.rec_down = True
							self.neighbour.rec_down = True
							# SUCCESSFUL BREAK
							break

					else:
						print('Received Corrupted ACK')
	 
 
 
				# SocketTimeout exception Handled.
				# throws exception for SocketTimeout
				except timeout:

					self.socket_timeout_counter += 1
					# if this is the first time entering the except block and has not received ACK yet, start the count down for connectivity timeout
					if(self.socket_timeout_counter == 1 and (self.any_ack_count == 0 or self.atleast_one_ack_received == False)):
						print('Countdown for connectivity timeout started')
						self.server_contact_start = time.time()
						self.packets_rec_after_timer = 0

					# If no packet is received Even after the specified time 
					if(time.time() - self.server_contact_start > max(self.server_contact_timeout, self.TIMEOUT) and self.any_ack_count == 0):
						self.fileTransferStatus.setMessage("Couldn't Reach Receiver. Detected atleast "+ str(self.server_contact_timeout) + " seconds Inactivity")                      
						self.rec_down = True # while loop of thread2 breaks if this is set to true
						self.neighbour.rec_down = True # while loop of thread1 breaks if this is set to true 
						# print("Couldn't Reach Receiver. Detected "+ str(self.server_contact_timeout) + " seconds Inactivity")                     
						break


					if(self.SYNrequest == 3 or self.neighbour.SYNrequest == 3):
						# If no packet is received Even after the specified time but N packets sent
						if(time.time() - self.last_any_ack_time > max(self.server_contact_timeout, self.TIMEOUT)):
							self.rec_down = True # while loop of thread2 breaks if this is set to true
							self.neighbour.rec_down = True # while loop of thread1 breaks if this is set to true 
							# UPDATE SUCCESS STATUS AND TERMINATE
							self.fileTransferStatus.setSuccess(True)
							self.fileTransferStatus.setMessage('File Transfer Successful')
							break

					else:
						# if time exceeded but no acks received within this time, then terminate
						if(time.time() - self.last_any_ack_time > max(self.server_contact_timeout, self.TIMEOUT) and self.atleast_one_ack_received == True):                      
							self.fileTransferStatus.setMessage("Receiver Went Down. Detected atleast "+ str(self.server_contact_timeout) + " seconds Inactivity")
							self.rec_down = True # while loop of thread2 breaks if this is set to true
							self.neighbour.rec_down = True # while loop of thread1 breaks if this is set to true
							# print("Receiver Went Down. Detected "+ str(self.server_contact_timeout) + " seconds Inactivity")
							break                   




					#TIMER
					print('Time out =', self.TIMEOUT)
					print('time difference is : ', time.time() - self.window_slide_time)
					if(time.time() - self.window_slide_time > self.TIMEOUT or self.ack_val == 0):
						

						if(self.itr > 0 and len(self.RTT) > 0):
							self.TIMEOUT = sum(self.RTT)/len(self.RTT)

						for i in ClientClassThread.sender_window:
							message_packet = i
							self.clientSocket.sendto(pickle.dumps(message_packet),(self.db.serverIP, self.db.serverPort))
							# BadNet.transmit(self.clientSocket, pickle.dumps(message_packet), self.db.serverIP, self.db.serverPort)
						
						print('Re-sent Window packets')

						# if waiting for SYN ACK = sent SYN don't know if it reached
						if(self.expected_ACK == self.db.segments_count+2 or (self.SYNrequest >= 2 or self.neighbour.SYNrequest >= 2) ):
							if(self.waitingToClose == False):
								# wait and terminate. Start timer. The next time reaches this, terminate.
								self.waitingToClose = True
							
							else:
								self.rec_down = True # while loop of thread2 breaks if this is set to true
								self.neighbour.rec_down = True # while loop of thread1 breaks if this is set to true                                
								# SUCCESSFUL But had to Wait and terminating
								# UPDATE SUCCESS STATUS AND TERMINATE
								self.fileTransferStatus.setSuccess(True)
								self.fileTransferStatus.setMessage('File Transfer Successful')
								break

				except OSError:
					print("Oops!", sys.exc_info()[0], "occured.")                   
					sys.exit()
				
				except SystemExit:
					print("Oops!", sys.exc_info()[0], "occured.")   
					sys.exit()
 
				except:
					print("2. Oops!", sys.exc_info(), "occured.")
					sys.exit()
 
				self.itr += 1


class ClientClassDataHandler:
 
	def divide_into_chunks(self, data, size, chunksize):
		if(size>chunksize):
			for i in range(0, size, chunksize):
				yield data[i:i+chunksize]
		else:
			yield data[0:size]
 
	def __init__(self, serverIP, serverPort, sendFile_name, sendFile_extension, storeFile_name, fileTransferStatus):
		self.serverIP = serverIP
		self.serverPort = serverPort
		self.sendFile_name = sendFile_name
		self.sendFile_extension = sendFile_extension
		self.storeFile_name = storeFile_name
		self.fileTransferStatus = fileTransferStatus
 
		self.sendFile_fopen = None
		self.sendFile_dataRead = "data read"
		self.sendFile_size = 0
		self.chunkSize = CHUNK_SIZE
		self.segments_count = 0
		self.message_segments = []
 
	def readData(self):
		# FILE HANDLING
		try :
			print('Processing data from', self.sendFile_name)
			# open file
			self.sendFile_fopen = open(self.sendFile_name, "rb")
			# read and store data
			self.sendFile_dataRead = self.sendFile_fopen.read()
			# close file
			self.sendFile_fopen.close()
 
		except:
			print("Oops!", sys.exc_info(), "occured.")  
		

		# PROCESSING
		self.sendFile_size = len(self.sendFile_dataRead)
		self.chunkSize = 90
		self.message_segments = list(self.divide_into_chunks(self.sendFile_dataRead, self.sendFile_size, self.chunkSize))
		self.segments_count = len(self.message_segments)
 
		file_size_bytes = os.path.getsize(self.sendFile_name)
		self.fileTransferStatus.setFileSize(file_size_bytes)
		self.fileTransferStatus.setNumOfPackets(self.segments_count + 2)
		# includes First and Last Packets (start, FIN)
 
class Sender():
 
	thread1 = None
	thread2 = None
	clientSocket = None
	datahandler = None
	pool_sema = None
	fileTransferStatus = None
	TIMEOUT = INITIAL_TIMEOUT #seconds
 
	def __init__(self,serverIP,serverPort,sendFile_name,sendFile_extension,storeFile_name):
		self.serverIP = serverIP
		self.serverPort = serverPort
		self.sendFile_name = sendFile_name
		self.sendFile_extension = sendFile_extension
		self.storeFile_name = storeFile_name
 
	def signal_handler(self,signal, frame):
		try: 
			self.thread1.stop()
			self.thread2.stop()
			sys.exit()
		except:     
			print("\nOops!", sys.exc_info()[0], "occured.")
			sys.exit()
 
	def run(self):
		print('Received Input Details')
 
		# 1. EXECUTION STATUS MANAGEMENT
		self.fileTransferStatus = executionDetails()
 
		self.fileTransferStatus.setIpFname(self.sendFile_name)
		self.fileTransferStatus.setOpFname(self.storeFile_name)
 
 
		# 2. PROCESS DATA
		self.datahandler = ClientClassDataHandler(self.serverIP, self.serverPort, self.sendFile_name, self.sendFile_extension, self.storeFile_name, self.fileTransferStatus)
		self.datahandler.readData()
 
		signal.signal(signal.SIGINT, self.signal_handler)
 
 
		# 3. CREATE AND MANAGE SOCKETS
 
		# create Client Socket
		self.clientSocket = socket(AF_INET, SOCK_DGRAM)
		self.clientSocket.settimeout(SOCKET_TIMEOUT) #seconds
 
		maxconnections = 1
		self.pool_sema = BoundedSemaphore(value=maxconnections)
 
		# create threads
 
		self.thread1 = ClientClassThread(1,self.TIMEOUT,self.pool_sema, self.datahandler,self.clientSocket, self.fileTransferStatus)
		self.thread2 = ClientClassThread(2,self.TIMEOUT,self.pool_sema, self.datahandler,self.clientSocket, self.fileTransferStatus)
 
		self.thread1.setNeighbours(self.thread2)
		self.thread2.setNeighbours(self.thread1)
 
		# self.thread1, self.thread2, self.clientSocket, self.myDataHandler = thread1, thread2, clientSocket, myDataHandler
 
		self.thread1.start()
		self.thread2.start()
 
		# Join threads
		self.thread1.join()
		self.thread2.join()
 
		# close client socket
		# print ("Closing Socket...")
		self.clientSocket.close()
 
		print(self.fileTransferStatus.getMessage())
		if(self.fileTransferStatus.getSuccess() == True):
			print('IUNPUT File Name/Path:',self.fileTransferStatus.getIpFname())
			print('INPUT File Size in Bytes:', self.fileTransferStatus.getFileSize())
			print('Number of Packets:',self.fileTransferStatus.getNumOfPackets())
			print('Transfer Time in seconds:',self.fileTransferStatus.getTime()) 
			print('Your file is expected to be stored as:',self.fileTransferStatus.getOpFname())
 
	# if(last_self.ack_val == self.db.segments_count+2):
	#   self.fileTransferStatus.setSuccess(True)
	#   self.fileTransferStatus.setEnd(time.time())
	#   self.fileTransferStatus.setTime()
	#   self.fileTransferStatus.setMessage('File Transfer Successful')                          
	#   break