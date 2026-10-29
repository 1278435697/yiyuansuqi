# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"D:\yisu-ai-platform\frontend\public\accessories\index.html",
         "/www/wwwroot/yisu/frontend/dist/accessories/index.html")
print("UP index.html")
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
print("css_ref:", run("grep -o 'styles.css?v=[^\"]*' /www/wwwroot/yisu/frontend/dist/accessories/index.html"))
cli.close()
