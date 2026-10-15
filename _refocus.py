# -*- coding: utf-8 -*-
"""重设今日焦点：全部清空后，取丝博最新3条置焦点，并验证库内资讯构成"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

code = r'''
import sys, logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
db = SessionLocal()
db.query(News).filter(News.is_focus.is_(True)).update({"is_focus": False})
db.commit()
fresh = db.query(News).filter(News.source == "中国丝绸博物馆").order_by(News.publish_time.desc(), News.id.desc()).limit(3).all()
for f in fresh:
    f.is_focus = True
db.commit()
print("焦点:")
for f in fresh:
    print("  -", f.publish_time.date() if f.publish_time else "?", f.title[:26], "img=" + ("Y" if f.cover_image else "N"))
print("---- 库内资讯构成 ----")
for src in ("中国丝绸博物馆", "敦煌研究院", "湖南博物院", "国家博物馆"):
    cnt = db.query(News).filter(News.source == src).count()
    print(" ", src, cnt)
db.close()
'''
cmd = f'cat > /tmp/_refocus.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_refocus.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(10)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
