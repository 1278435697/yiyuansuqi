# -*- coding: utf-8 -*-
"""上传 websearch.py + home.py，重启并验证过滤效果"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\websearch.py', '/www/wwwroot/yisu/backend/app/api/websearch.py')
sftp.put(r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\home.py', '/www/wwwroot/yisu/backend/app/api/home.py')
sftp.close()
print('uploaded')

_, out, err = cli.exec_command(f'{PY} -m py_compile /www/wwwroot/yisu/backend/app/api/websearch.py /www/wwwroot/yisu/backend/app/api/home.py && echo PYOK')
print(out.read().decode('utf-8','replace').strip())
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])

cli.exec_command("pkill -f 'uvicorn.*app.main:app' ; sleep 2 ; cd /www/wwwroot/yisu/backend && setsid nohup ./591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/yisu_api.log 2>&1 &")
print('restart issued, sleeping 22s...')
cli.close()
time.sleep(22)

cli2 = paramiko.SSHClient()
cli2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli2.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, _ = cli2.exec_command("curl -s -H 'Host: 47.93.14.11' http://127.0.0.1:8765/health")
print('health:', out.read().decode('utf-8','replace').strip())
cli2.close()
print('=== DONE ===')
