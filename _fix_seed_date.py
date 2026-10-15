# -*- coding: utf-8 -*-
"""查库内资讯 source 分布，种子日期改旧让丝博置前"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

code = r'''
import sys, logging, datetime
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
db = SessionLocal()
from sqlalchemy import func
rows = db.query(News.source, func.count(News.id)).group_by(News.source).all()
print("SOURCES:", rows)
# 种子源（非丝博）日期统一改旧，让真实抓取的丝博资讯排前面
seed_sources = [s for s, c in rows if s != "中国丝绸博物馆"]
old = datetime.datetime(2026, 8, 1)
n = db.query(News).filter(News.source.in_(seed_sources), News.publish_time > old).update({"publish_time": old})
db.commit()
print("种子日期下调:", n)
# 重新验证首页将显示的前8条
for x in db.query(News).order_by(News.publish_time.desc(), News.id.desc()).limit(8).all():
    print("  -", x.publish_time.date() if x.publish_time else "?", x.source, x.title[:22], "img=" + ("Y" if x.cover_image else "N"))
db.close()
'''
cmd = f'cat > /tmp/_fix_seed_date.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_fix_seed_date.py 2>&1'
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
