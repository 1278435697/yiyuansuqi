# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c):
    i,o,e = cli.exec_command(c, timeout=20)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
print("=== .env ===")
print(run("cat /www/wwwroot/yisu/backend/.env 2>/dev/null | grep -iE 'LLM|MODEL|API_KEY|BASE_URL' | sed 's/=.*key.*/=***/I'"))
print("=== systemd env ===")
print(run("systemctl cat yisu-backend 2>/dev/null | grep -iE 'Environment|LLM|MODEL' | head -10"))
cli.close()
