# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
print(run("grep -rn 'api' /www/server/panel/vhost/nginx/*.conf 2>/dev/null | grep -iE 'location|proxy_pass' | head -20"))
print("---")
print(run("ls /www/server/panel/vhost/nginx/ | grep -i yisu"))
cli.close()
