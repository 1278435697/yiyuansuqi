# -*- coding: utf-8 -*-
# 探测服务器后端运行方式
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print("== uvicorn 进程 ==")
print(run("ps -ef | grep -i uvicorn | grep -v grep | head -5") or "(none)")
print("== 监听 8765 ==")
print(run("ss -ltnp | grep 8765 || netstat -ltnp 2>/dev/null | grep 8765") or "(none)")
print("== python 候选 ==")
print(run("ls /www/server/python/bin/python 2>/dev/null; which python3; ls /www/wwwroot/yisu/backend/*.sh 2>/dev/null; cat /www/wwwroot/yisu/backend/start.sh 2>/dev/null | head -10"))
cli.close()
print("=== DONE ===")
