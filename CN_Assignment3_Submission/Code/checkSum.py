def myCheckSum(data):
	try:
		sum = 0
		for i in range(0,len(data),2):
			if i + 1 >= len(data):
				sum += ord(data[i]) & 0xFF
			else:
				w = ((ord(data[i]) << 8) & 0xFF00) + (ord(data[i+1]) & 0xFF)
				sum += w
		while (sum >> 16) > 0:
			sum = (sum & 0xFFFF) + (sum >> 16)
		return ~sum & 0xFFFF
	except OSError:
		print('checksum ------- Returning false')
		return 'False'