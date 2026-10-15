# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging, re; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from app.db.database import SessionLocal
from app.db.models import News
from collections import Counter
db=SessionLocal()
rows=db.query(News).all()
dom=Counter()
for n in rows:
    u=n.source_url or ''
    m=re.search(r'https?://([^/]+)', u)
    dom[(m.group(1) if m else '?')[:40]] += 1
print('TOTAL=', len(rows))
for d,c in dom.most_common(40): print(c, d)
db.close()
" 2>&1""")[:2000])
cli.close()
print("=== DONE ===")
