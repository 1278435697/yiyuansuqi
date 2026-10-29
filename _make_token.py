import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
code = (
    "cd /www/wwwroot/yisu/backend && "
    "/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c \""
    "from datetime import datetime, timedelta; "
    "from jose import jwt; "
    "payload={'sub':'1','role':'admin','exp':datetime.utcnow()+timedelta(days=7)}; "
    "print(jwt.encode(payload, 'yisu-6616dea7437e483d99a69c549cbf7efc', algorithm='HS256'))\""
)
stdin, stdout, stderr = c.exec_command(code)
print(stdout.read().decode().strip())
err = stderr.read().decode()
if err:
    print("ERR:", err[-300:])
c.close()
