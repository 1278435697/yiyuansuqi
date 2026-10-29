import paramiko
host="47.93.14.11"; user="root"; pw="Han050607@"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pw, timeout=30)
def run(cmd):
    stdin,stdout,stderr=ssh.exec_command(cmd, timeout=60)
    out = stdout.channel.recv(65535).decode('utf-8','ignore')
    err = stderr.channel.recv(65535).decode('utf-8','ignore')
    return (out+err).strip()
print("reload:", run("nginx -s reload 2>&1; sleep 1; echo RELOAD_DONE"))
print("headers:", run("curl -s -H 'Host: 47.93.14.11' -I http://127.0.0.1/museum/assets/index-DOlOnALt.js | grep -i -E 'cache-control|expires'"))
ssh.close()
