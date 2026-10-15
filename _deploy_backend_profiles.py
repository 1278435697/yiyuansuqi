# -*- coding: utf-8 -*-
"""同步 31 种档案后端并重启 uvicorn"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
REMOTE_API = '/www/wwwroot/yisu/backend/app/api'
FILES = [
    (r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric_profiles.py', 'fabric_profiles.py'),
    (r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric.py', 'fabric.py'),
]

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)

def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

sftp = cli.open_sftp()
for lp, rn in FILES:
    sftp.put(lp, REMOTE_API + '/' + rn)
    print('uploaded', rn)
sftp.close()

print('pycheck:', run('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "import ast; ast.parse(open(\'/www/wwwroot/yisu/backend/app/api/fabric_profiles.py\').read()); ast.parse(open(\'/www/wwwroot/yisu/backend/app/api/fabric.py\').read()); print(\'OK\')"').strip())

print(run('pkill -f "uvicorn app.main:app" || true').strip() or '(pkill ok)')
time.sleep(2)
# 后台启动：发出后立即断开（paramiko 读后台输出必超时）
cli.exec_command('cd /www/wwwroot/yisu/backend && setsid nohup /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/uvicorn_profiles.log 2>&1 < /dev/null &')
cli.close()
print('started, sleep 22...')
time.sleep(22)

cli2 = paramiko.SSHClient()
cli2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli2.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)
def run2(c, t=60):
    i, o, e = cli2.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print('health:', run2('curl -s -H "Host: 47.93.14.11" http://127.0.0.1:8765/health').strip())
cli2.close()
print('=== DONE ===')
