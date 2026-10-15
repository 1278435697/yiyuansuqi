# -*- coding: utf-8 -*-
"""查 news 表 source 分布与焦点状态"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
code = r'''
import sys
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
from sqlalchemy import func
db = SessionLocal()
try:
    rows = db.query(News.source, func.count(News.id)).group_by(News.source).all()
    print("SOURCES:", rows)
    foc = db.query(News.id, News.title, News.source, News.is_focus).filter(News.is_focus.is_(True)).order_by(News.id.desc()).limit(8).all()
    print("FOCUS:", [(f.id, f.title[:26], f.source, f.is_focus) for f in foc])
    latest = db.query(News).order_by(News.publish_time.desc(), News.id.desc()).limit(5).all()
    print("LATEST:", [(x.id, x.title[:22], x.publish_time, x.source, x.is_focus) for x in latest])
finally:
    db.close()
'''
cmd = f'cat > /tmp/_check_news.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_check_news.py 2>&1'
_, out, err = cli.exec_command(cmd)
time.sleep(3)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
