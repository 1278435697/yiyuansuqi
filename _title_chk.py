# -*- coding: utf-8 -*-
import re, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("=== museum/index.html title ===")
out.append(run("grep -o '<title>[^<]*</title>' /www/wwwroot/yisu/frontend/dist/museum/index.html"))
out.append("=== index chunk title 相关 ===")
out.append(run("grep -o 'document.title=[^;]*' /www/wwwroot/yisu/frontend/dist/museum/assets/index-BqJJw04H.js | head -5"))
out.append("=== MuseumView title 设置 ===")
out.append(run("grep -o 'document.title=[^;]*' /www/wwwroot/yisu/frontend/dist/museum/assets/MuseumView-aROHavN7.js | head -5"))
out.append("=== 全目录搜 衣溯AI ===")
out.append(run("grep -rl '衣溯AI' /www/wwwroot/yisu/frontend/dist/museum 2>/dev/null | head -10"))
cli.close()
open(r"D:\yisu-ai-platform\_title_chk.txt","w",encoding="utf-8").write("\n".join(out))
