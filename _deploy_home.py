# -*- coding: utf-8 -*-
"""部署 home.py（焦点独立返回）+ 重启后端"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL = r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app'
REMOTE = '/www/wwwroot/yisu/backend/app'
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(f'{LOCAL}\\api\\home.py'.replace('\\', '/'), f'{REMOTE}/api/home.py')
sftp.close()
_, out, err = cli.exec_command(f'{PY} -m py_compile {REMOTE}/api/home.py && echo PYOK')
print(out.read().decode('utf-8','replace').strip())
# 重启后端（systemd 服务名探测）
_, out, err = cli.exec_command('systemctl list-units --type=service --no-pager | grep -iE "yisu|fastapi|uvicorn|gunicorn" | head -5')
print("SVC:", out.read().decode('utf-8','replace').strip() or "none")
cli.close()
print('=== DONE ===')
