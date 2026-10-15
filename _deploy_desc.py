# -*- coding: utf-8 -*-
"""更新云数据库 31 种面料 description + 同步后端 fabric_profiles.py/fabric.py 并重启"""
import paramiko, io, sys, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
PROFILES_JSON = r'C:\Users\lenovo\Desktop\yisu-ai-platform\_profiles_31.json'
REMOTE_API = '/www/wwwroot/yisu/backend/app/api'

profiles = json.load(open(PROFILES_JSON, encoding='utf-8'))

SERVER_PY = '''# -*- coding: utf-8 -*-
import json, pymysql
profiles = json.load(open('/tmp/profiles31.json', encoding='utf-8'))
NAME_MAP = {'兽皮': '兽皮毛皮'}
c = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='han050607',
                    database='yisu_ai', charset='utf8mb4')
cur = c.cursor()
n = 0
for p in profiles:
    db_name = NAME_MAP.get(p['name'], p['name'])
    cur.execute('UPDATE fabrics SET description=%s WHERE name=%s', (p['description'], db_name))
    n += cur.rowcount
c.commit(); c.close()
print('updated', n)
'''

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)

def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

# 1. 数据库 UPDATE
sftp = cli.open_sftp()
with sftp.open('/tmp/profiles31.json', 'w') as f:
    f.write(json.dumps(profiles, ensure_ascii=False))
with sftp.open('/tmp/upd_desc.py', 'w') as f:
    f.write(SERVER_PY)
sftp.close()
print('db:', run('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/upd_desc.py', 60).strip())

# 2. 后端文件上传
sftp = cli.open_sftp()
sftp.put(r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric_profiles.py', REMOTE_API + '/fabric_profiles.py')
sftp.put(r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric.py', REMOTE_API + '/fabric.py')
sftp.close()
print('uploaded backend files')

# 3. 重启
print('pycheck:', run('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "import ast; ast.parse(open(\'/www/wwwroot/yisu/backend/app/api/fabric_profiles.py\').read()); print(\'OK\')"').strip())
print(run('pkill -f "uvicorn app.main:app" || true').strip() or '(pkill ok)')
time.sleep(2)
cli.exec_command('cd /www/wwwroot/yisu/backend && setsid nohup /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/uvicorn_desc.log 2>&1 < /dev/null &')
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
