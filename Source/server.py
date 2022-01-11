#!/usr/bin/env python3

from datetime import datetime
import socket
import ssl

HOST = '127.0.0.1'
PORT = 65432

def search():
    i = str(input("Geben Sie einen Suchbegriff ein: "))
    l = []
    f = open("Source/data/" + "size_" + datetime.now().strftime("%d_%m_%Y"),"r", encoding="utf-8")
    for line in f:
        if i in line:
            l.append(line[:-2])
    return l

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('./cert/cert.pem', './cert/key.pem')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    with context.wrap_socket(s, server_side=True) as ssock:
        while True:
            print("Waiting for new device\n")
            conn, addr = ssock.accept()
            with conn:
                print("A new device connected:", addr)
                while True:
                    print("\nList of actions: \n1. Get Tree \n2. Filetypes\n3. Filesize\n4. Search\n5. Close\n")
                    i = int(input("Choose action: "))
                    conn.sendall(bytes([i]))
                    if i == 1:
                        print("Receiving Data")
                        f = open("Source/data/" + "tree_" + datetime.now().strftime("%d_%m_%Y"),"w", encoding="utf-8")
                        line = ""
                        while line != "!":
                            line = (conn.recv(1024)).decode()
                            f.write(line)
                        f.close()
                    elif i == 2:
                        print("Receiving Data")
                        f = open("Source/data/" + "type_" + datetime.now().strftime("%d_%m_%Y"),"w", encoding="utf-8")
                        line = ""
                        while line != "!":
                            line = (conn.recv(1024)).decode()
                            f.write(line)
                        f.close()   
                    elif i == 3:
                        print("Receiving Data")
                        f = open("Source/data/" + "size_" + datetime.now().strftime("%d_%m_%Y"),"w", encoding="utf-8") # write sorted by size to file
                        line = ""
                        while line != "!":
                            line = (conn.recv(1024)).decode()
                            f.write(line)
                        f.close() 
                    elif i == 4:
                        ss = str(input("Enter search string: "))
                        f = open("Source/data/" + ss + "_" + datetime.now().strftime("%d_%m_%Y"),"w", encoding="utf-8")
                        conn.sendall(ss.encode())
                        line = ""
                        while line != "!":
                            line = (conn.recv(1024)).decode()
                            f.write(line)    
                        f.close()
                    else: break
                conn.sendall(("Connection closed by server.").encode())
                print("Device ", addr, " disconnected.")
