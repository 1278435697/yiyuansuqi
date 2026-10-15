# -*- coding: utf-8 -*-
"""修正 id=7 来源为'国家博物馆'，与内容一致"""
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
n = db.query(News).filter(News.id == 7).first()
if n:
    n.source = "国家博物馆"
    db.commit()
    print("已修正:", n.id, n.source, n.title[:20])
db.close()
'''
cmd = f'cat > /tmp/_fix7.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_fix7.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(8)
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
