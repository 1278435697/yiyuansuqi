# -*- coding: utf-8 -*-
# 第三轮回填：summary 与 content 重叠的条目，用 AI 独立生成 200-300 字摘要（区别于正文）
import paramiko, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REMOTE_PY = r'''# -*- coding: utf-8 -*-
import sys, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, '/www/wwwroot/yisu/backend')
from app.db.database import SessionLocal
from app.db.models import News
from app.ai_engine.news_fetcher import _ai_summary
db = SessionLocal()
rows = db.query(News).all()
updated = 0
for n in rows:
    s = (n.summary or '').strip()
    c = (n.content or '').strip()
    if not s or not c:
        continue
    overlap = (s[:120] == c[:120]) or (s == c) or (s and c and s in c)
    if not overlap:
        continue
    ai = _ai_summary(n.title or '', n.source or '', n.publish_time)
    if ai and ai != s:
        n.summary = ai[:600]
        updated += 1
        print('SUM', n.id, '|', (n.title or '')[:22], '| new=', len(n.summary))
    if updated >= 500:
        db.commit()
        updated = 0
db.commit()
print('TOTAL=', updated)
db.close()
'''
b64 = base64.b64encode(REMOTE_PY.encode('utf-8')).decode()
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=900):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
cmd = "echo %s | base64 -d > /tmp/backfill3.py && cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/backfill3.py 2>&1" % b64
print(run(cmd, 900)[:3000])
cli.close()
print("=== DONE ===")
