# -*- coding: utf-8 -*-
import io, sys, paramiko, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.get("/www/wwwroot/yisu/frontend/dist/museum/assets/assets.manifest.json", r"D:\yisu-ai-platform\_dl\assets.manifest.json")
sftp.close()
data = open(r"D:\yisu-ai-platform\_dl\assets.manifest.json", encoding='utf-8', errors='replace').read()
hits = [m.start() for m in re.finditer('衣溯AI', data)]
print("hits:", len(hits))
for h in hits[:5]:
    print("ctx:", data[max(0,h-50):h+50].replace("\n"," "))
cli.close()
