# -*- coding: utf-8 -*-
"""查'国博唐代陶俑'记录来源字段，便于修正来源标注"""
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
rows = db.query(News).filter(News.title.contains("圆领袍")).all()
for n in rows:
    print("id:", n.id, "| source:", n.source, "| url:", (n.source_url or "")[:60])
    print("  title:", n.title)
    print("  cover:", (n.cover_image or "")[:70])
db.close()
'''
cmd = f'cat > /tmp/_q.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_q.py 2>&1'
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
