#!/usr/bin/env python3

from pathlib import Path
import socket
import ssl

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

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
context.load_verify_locations('./../cert/cert.pem')
conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname="localhost")
conn.connect(("localhost", 65432))

data = conn.recv(1024)
i = int.from_bytes(data, "big")
while i != 5:
    print("Datatransfer starting")
    if i == 1:
        for line in tree(Path.home()):
            conn.sendall((line + "\n").encode())
        conn.sendall(("!").encode())
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
            conn.sendall(("!").encode())

        if i == 3:
            for x, y in ordered_size.items():
                if y > 50000: # only files with a size over 50000
                    conn.sendall((str(x) + ", " + str(y) + "\n").encode())
            conn.sendall(("!").encode())

        if i == 4:
            ss = (conn.recv(1024)).decode()
            for x, y in files_dict_type.items():
                if ss in str(x):
                    conn.sendall((str(x) + "\n").encode())
            conn.sendall(("!").encode())

    data = conn.recv(1024)
    i = int.from_bytes(data, "big")

endmessage = conn.recv(1024)
print(endmessage.decode())