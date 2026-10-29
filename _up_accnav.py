# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
# 备份线上原版
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
run("cp /www/wwwroot/yisu/frontend/dist/accessories/styles.css /tmp/styles.css.bak_navfix")
sftp.put(r"D:\yisu-ai-platform\frontend\public\accessories\styles.css",
         "/www/wwwroot/yisu/frontend/dist/accessories/styles.css")
print("UP styles.css")
sftp.close()
# 验证断点已改
print("media_block:", run("grep -A4 'max-width: 1120px' /www/wwwroot/yisu/frontend/dist/accessories/styles.css | head -8"))
cli.close()
