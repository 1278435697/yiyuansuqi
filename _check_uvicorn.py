import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = "ps aux | grep uvicorn | grep -v grep; echo '---LOG---'; tail -30 /tmp/uvicorn.log"
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
c.close()
