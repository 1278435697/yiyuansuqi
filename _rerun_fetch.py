# -*- coding: utf-8 -*-
"""重新上传 news_fetcher.py 并重跑，验证今日焦点滚动更新"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL = r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app'
REMOTE = '/www/wwwroot/yisu/backend/app'
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(f'{LOCAL}\\ai_engine\\news_fetcher.py'.replace('\\', '/'), f'{REMOTE}/ai_engine/news_fetcher.py')
sftp.close()
print('uploaded news_fetcher.py')
_, out, err = cli.exec_command(f'{PY} -m py_compile {REMOTE}/ai_engine/news_fetcher.py && echo PYOK')
print(out.read().decode('utf-8','replace').strip())
_, out, err = cli.exec_command(f"cd /www/wwwroot/yisu/backend && {PY} app/ai_engine/news_fetcher.py 2>&1")
time.sleep(10)
print(out.read().decode('utf-8','replace').strip())
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
