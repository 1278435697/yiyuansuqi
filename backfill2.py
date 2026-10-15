# -*- coding: utf-8 -*-
# 回填：为 content 为空 / summary 与正文重叠的存量新闻补完整正文 + AI 独立摘要
import paramiko, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REMOTE_PY = r'''# -*- coding: utf-8 -*-
import sys, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, '/www/wwwroot/yisu/backend')
from app.db.database import SessionLocal
from app.db.models import News
from app.ai_engine.news_fetcher import fetch_detail, _ai_summary
db = SessionLocal()
rows = db.query(News).all()
updated = 0
for n in rows:
    if not (n.source_url or '').startswith('http'):
        continue
    need = (not n.content) or (n.summary and n.content and n.summary[:200] in (n.content[:200] or ''))
    if not need:
        continue
    try:
        date, summary, cover, full = fetch_detail(n.source_url, n.title or '')
    except Exception:
        date, summary, cover, full = None, '', '', ''
    changed = False
    if full and len(full) > 40 and (not n.content or len(full) > len(n.content or '')):
        n.content = full[:4000]
        changed = True
    if summary and len(summary) > len(n.summary or '') and summary != n.title:
        n.summary = summary[:500]
        changed = True
    if (not n.summary or len(n.summary) < 40) and n.title:
        ai = _ai_summary(n.title, n.source or '', date)
        if ai:
            n.summary = ai[:600]
            changed = True
    if changed:
        updated += 1
        print('UP', n.id, '|', (n.title or '')[:22], '| content=', len(n.content or ''), '| summary=', len(n.summary or ''))
    if updated >= 500:
        db.commit()
        updated = 0
db.commit()
print('BATCH_DONE')
db.close()
'''
b64 = base64.b64encode(REMOTE_PY.encode('utf-8')).decode()
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=900):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
cmd = "echo %s | base64 -d > /tmp/backfill2.py && cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/backfill2.py 2>&1" % b64
print(run(cmd, 900)[:3500])
cli.close()
print("=== DONE ===")
