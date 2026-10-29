# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("files=" + run("grep -rl '衣溯AI' /www/wwwroot/yisu/frontend/dist/museum 2>/dev/null"))
out.append("ctx=" + run("grep -o '.\{40\}衣溯AI.\{40\}' /www/wwwroot/yisu/frontend/dist/museum/$(grep -rl '衣溯AI' /www/wwwroot/yisu/frontend/dist/museum 2>/dev/null | head -1) 2>/dev/null | head -3"))
cli.close()
open(r"D:\yisu-ai-platform\_resid.txt","w",encoding="utf-8").write("\n".join(out))
