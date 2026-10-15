# -*- coding: utf-8 -*-
"""查丝博最新 publish_time + cron 日志"""
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
rows = db.query(News).filter(News.source == "中国丝绸博物馆").all()
rows.sort(key=lambda x: x.id, reverse=True)
print("丝博最新8条(publish_time):")
for n in rows[:8]:
    print("  id", n.id, "|", (n.publish_time.date().isoformat() if n.publish_time else "?"), "|", n.title[:30])
print("全库按时间倒序前5:")
allr = sorted(db.query(News).all(), key=lambda x: x.publish_time or __import__("datetime").datetime.min, reverse=True)[:5]
for n in allr:
    print("  ", n.publish_time.date().isoformat() if n.publish_time else "?", "|", n.title[:28])
db.close()
'''
cmd = f'cat > /tmp/_time.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_time.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(8)
print(out.read().decode('utf-8','replace'))
_, out, err = cli.exec_command("ls -la /tmp/yisu_news_fetch.log 2>&1; echo '---'; tail -5 /tmp/yisu_news_fetch.log 2>&1")
print("CRON_LOG:", out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
