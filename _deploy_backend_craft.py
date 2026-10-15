# -*- coding: utf-8 -*-
"""同步面料工艺数据到云端后端并重启 uvicorn"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
REMOTE_API = '/www/wwwroot/yisu/backend/app/api'
FILES = [
    (r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\craft_profiles.py', 'craft_profiles.py'),
    (r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric.py', 'fabric.py'),
]

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)

def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

# 1. 上传文件
sftp = cli.open_sftp()
for lp, rn in FILES:
    sftp.put(lp, REMOTE_API + '/' + rn)
    print('uploaded', rn)
sftp.close()

# 2. 语法检查
print('pycheck:', run('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "import ast; ast.parse(open(\'/www/wwwroot/yisu/backend/app/api/craft_profiles.py\').read()); ast.parse(open(\'/www/wwwroot/yisu/backend/app/api/fabric.py\').read()); print(\'OK\')"').strip())

# 3. 重启 uvicorn（后台启动，不阻塞等待输出）
print(run('pkill -f "uvicorn app.main:app" || true').strip() or '(pkill ok)')
time.sleep(2)
print(run('cd /www/wwwroot/yisu/backend && setsid nohup /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/uvicorn_craft.log 2>&1 < /dev/null & echo started').strip() or '(start ok)')
cli.close()
print('sleep 22 for boot...')
time.sleep(22)

# 4. 验证：health + list 返回 craft
cli2 = paramiko.SSHClient()
cli2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli2.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)
def run2(c, t=60):
    i, o, e = cli2.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print('health:', run2('curl -s -H "Host: 47.93.14.11" http://127.0.0.1:8765/health').strip())
print('list-check:', run2('curl -s -H "Host: 47.93.14.11" http://127.0.0.1:8765/api/fabrics/list | /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d[\'items\'])); [print(i[\'name\'], bool(i.get(\'craft\'))) for i in d[\'items\'][:6]]"').strip())
cli2.close()
print('=== DONE ===')
