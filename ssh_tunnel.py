import paramiko, socket, threading, time, sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.93.14.11', username='root', password='Han050607@')
transport = ssh.get_transport()

def forward(local_port, remote_host, remote_port):
    ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind(('127.0.0.1', local_port))
    ssock.listen(50)
    print(f"隧道: 127.0.0.1:{local_port} -> {remote_host}:{remote_port}")
    while True:
        csock, _ = ssock.accept()
        chan = transport.open_channel('direct-tcpip', (remote_host, remote_port), csock.getpeername())
        if chan is None:
            csock.close()
            continue
        def pipe(a, b):
            while True:
                d = a.recv(4096)
                if not d: break
                b.send(d)
            a.close(); b.close()
        threading.Thread(target=pipe, args=(csock, chan), daemon=True).start()
        threading.Thread(target=pipe, args=(chan, csock), daemon=True).start()

threading.Thread(target=forward, args=(3306, '127.0.0.1', 3306), daemon=True).start()
print("隧道已建立，保持运行...")
while True:
    time.sleep(60)
