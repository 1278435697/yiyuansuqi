# -*- coding: utf-8 -*-
"""删除库内故宫公告类资讯（保留展览/活动/研究类），验证删除后列表"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

code = r'''
import sys, logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News

BAN = ("公告", "声明", "暂停", "延期", "闭馆", "施工", "停止开放", "恢复开放", "开放时间", "招聘", "须知", "中标", "招标", "成交")
db = SessionLocal()
q = db.query(News).filter(News.source == "故宫博物院")
rows = q.all()
deleted = 0
for n in rows:
    if any(w in n.title for w in BAN):
        db.delete(n)
        deleted += 1
db.commit()
print("删除公告:", deleted)
print("删除后故宫资讯:", db.query(News).filter(News.source == "故宫博物院").count())
for x in db.query(News).filter(News.source == "故宫博物院").order_by(News.publish_time.desc(), News.id.desc()).all():
    print("  -", x.publish_time.date() if x.publish_time else "?", x.title[:22], "img=" + ("Y" if x.cover_image else "N"))
db.close()
'''
cmd = f'cat > /tmp/_del_announce.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_del_announce.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(12)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
