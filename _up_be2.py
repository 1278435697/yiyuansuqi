# -*- coding: utf-8 -*-
import io, sys, paramiko, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"D:\yisu-ai-platform\backend\app\api\ai_qa.py","/www/wwwroot/yisu/backend/app/api/ai_qa.py")
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
print(run("systemctl restart yisu-backend")); time.sleep(4)
print(run("systemctl is-active yisu-backend"))
cli.close()
