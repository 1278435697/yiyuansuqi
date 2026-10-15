# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print("== 进程 ==")
print(run("ps -ef | grep uvicorn | grep -v grep | head -3") or "(none)")
print("== 日志尾 ==")
print((run("tail -20 /tmp/yisu_api.log") or "(no log)")[:1500])
print("== 接口 ==")
print(run("curl -s -m 10 'http://127.0.0.1:8765/api/home/news?page_size=5' | head -c 800")[:800])
cli.close()
print("=== DONE ===")
