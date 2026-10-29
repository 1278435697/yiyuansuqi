# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
for f, r in [("index.html", "/www/wwwroot/yisu/frontend/dist/museum/index.html"),
             ("exhibits-Cb5qGZIp.js", "/www/wwwroot/yisu/frontend/dist/museum/assets/exhibits-Cb5qGZIp.js"),
             ("assets.manifest.json", "/www/wwwroot/yisu/frontend/dist/museum/assets/assets.manifest.json")]:
    sftp.get(r, rf"D:\yisu-ai-platform\_dl\{f}")
    print("DL", f)
sftp.close()
cli.close()
# 查看 exhibits 与 manifest 中衣溯AI 上下文
import re
for f in ["exhibits-Cb5qGZIp.js", "assets.manifest.json"]:
    data = open(rf"D:\yisu-ai-platform\_dl\{f}", encoding='utf-8', errors='replace').read()
    hits = [m.start() for m in re.finditer('衣溯AI', data)]
    print("==", f, "hits:", len(hits))
    for h in hits[:3]:
        print("   ctx:", data[max(0,h-40):h+40].replace("\n"," "))
