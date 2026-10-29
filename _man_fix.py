# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
f = r"D:\yisu-ai-platform\_dl\assets.manifest.json"
data = open(f, encoding='utf-8').read()
n = data.count("衣溯AI 主站文物影像库")
data = data.replace("衣溯AI 主站文物影像库", "衣溯 主站文物影像库")
open(f, "w", encoding="utf-8", newline="").write(data)
print("replaced:", n)
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(f, "/www/wwwroot/yisu/frontend/dist/museum/assets/assets.manifest.json")
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=60)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
print("residual_all=" + run("grep -rl '衣溯AI' /www/wwwroot/yisu/frontend/dist/museum 2>/dev/null | wc -l"))
cli.close()
