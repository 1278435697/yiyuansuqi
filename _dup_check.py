# -*- coding: utf-8 -*-
"""检查资讯总数、丝博条数、重复标题"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
code = r'''
import sys, logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
from collections import Counter
db = SessionLocal()
rows = db.query(News).all()
print("总条数:", len(rows))
print("丝博条数:", sum(1 for n in rows if n.source == "中国丝绸博物馆"))
c = Counter(n.title for n in rows)
dups = {t: k for t, k in c.items() if k > 1}
print("重复标题数:", len(dups))
for t, k in list(dups.items())[:5]:
    print("  重复:", k, "x", t[:30])
ids = sorted(n.id for n in rows)
print("id范围:", ids[0], "-", ids[-1])
print("最新5条:")
for n in sorted(rows, key=lambda x: x.id, reverse=True)[:5]:
    print("  id", n.id, "|", n.title[:26], "|", n.source)
db.close()
'''
cmd = f'cat > /tmp/_dup.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_dup.py 2>&1'
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
