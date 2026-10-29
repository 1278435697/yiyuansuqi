# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"D:\yisu-ai-platform\backend\app\api\ai_qa.py",
         "/www/wwwroot/yisu/backend/app/api/ai_qa.py")
print("UP OK")
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
# 找后端服务名并重启
print("=== services ===")
print(run("systemctl list-units --type=service | grep -iE 'yisu|uvicorn|fastapi|gunicorn' "))
print("=== restart ===")
print(run("systemctl restart yisu-backend 2>&1 || (ps aux | grep -E 'uvicorn|main:app' | grep -v grep)"))
import time; time.sleep(4)
print("=== status ===")
print(run("systemctl status yisu-backend --no-pager 2>&1 | head -8 || curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/docs"))
cli.close()
