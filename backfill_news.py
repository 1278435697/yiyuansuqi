# -*- coding: utf-8 -*-
# 服务器补全脚本：对库存中无封面图/摘要过短的新闻重新抓详情（封面+长摘要）
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
    need = (not n.cover_image) or (not n.summary) or len(n.summary) < 300
    if not need:
        continue
    try:
        date, summary, cover = fetch_detail(n.source_url or '', n.title or '')
    except Exception:
        date, summary, cover = None, '', ''
    changed = False
    if cover and (not n.cover_image):
        n.cover_image = cover[:255]
        changed = True
    if summary and len(summary) > len(n.summary or ''):
        n.summary = summary[:500]
        changed = True
    if (not n.summary or len(n.summary) < 40) and n.title:
        ai = _ai_summary(n.title, n.source or '', date)
        if ai:
            n.summary = ai[:600]
            changed = True
    if date and n.publish_time:
        pass
    if changed:
        updated += 1
        print('UP', n.id, '|', (n.title or '')[:24], '| cover=', bool(n.cover_image), '| len=', len(n.summary or ''))
    if updated >= 400:
        db.commit()
db.commit()
print('TOTAL_UPDATED=', updated)
db.close()
'''
b64 = base64.b64encode(REMOTE_PY.encode('utf-8')).decode()
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=600):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
cmd = "echo %s | base64 -d > /tmp/backfill_news.py && cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/backfill_news.py 2>&1" % b64
print(run(cmd, 600)[:4000])
cli.close()
print("=== DONE ===")
