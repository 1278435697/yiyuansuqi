# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"D:\yisu-ai-platform\frontend\public\accessories\styles.css",
         "/www/wwwroot/yisu/frontend/dist/accessories/styles.css")
sftp.put(r"D:\yisu-ai-platform\frontend\public\accessories\index.html",
         "/www/wwwroot/yisu/frontend/dist/accessories/index.html")
print("UP OK")
sftp.close(); cli.close()
