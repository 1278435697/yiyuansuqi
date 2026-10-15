# -*- coding: utf-8 -*-
"""查 is_focus 条数与内容"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
code = r'''
import sys, logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
db = SessionLocal()
rows = db.query(News).filter(News.is_focus == True).order_by(News.publish_time.desc()).all()
print("焦点条数:", len(rows))
for n in rows:
    print("  id", n.id, "|", n.title[:30], "|", n.publish_time.date() if n.publish_time else "?")
db.close()
'''
cmd = f'cat > /tmp/_focus.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_focus.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(8)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
