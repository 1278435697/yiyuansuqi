import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = "grep -i jwt /www/wwwroot/yisu/backend/.env 2>/dev/null; echo '---'; grep -i jwt /www/wwwroot/yisu/backend/app/core/config.py | head -5"
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
c.close()
