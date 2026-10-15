# -*- coding: utf-8 -*-
# 第四轮回填：① 清掉正文中的页脚噪音（京ICP备/京公网安备/网站维护/联系方式/©等）
# ② 对摘要仍是"信息不足"拒绝文案或与正文重叠的条目，用带正文的 AI 独立生成摘要
import paramiko, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REMOTE_PY = r'''# -*- coding: utf-8 -*-
import sys, logging, re
logging.disable(logging.CRITICAL)
sys.path.insert(0, '/www/wwwroot/yisu/backend')
from app.db.database import SessionLocal
from app.db.models import News
from app.ai_engine.news_fetcher import fetch_detail, _ai_summary
db = SessionLocal()
rows = db.query(News).all()
updated = 0
def clean_footer(txt):
    if not txt:
        return txt
    txt = re.sub(r"网站维护[：:].*?(联系方式|$)", " ", txt)
    txt = re.sub(r"联系方式[：:][^\s，。,；;]+", " ", txt)
    txt = re.sub(r"京ICP备[0-9A-Za-z-]+号?", " ", txt)
    txt = re.sub(r"京公网安备[0-9A-Za-z]+号?", " ", txt)
    txt = re.sub(r"©.*?$", "", txt)
    txt = re.sub(r"备案号[^\s，。,；;]*", " ", txt)
    txt = re.sub(r"网站建设[：:][^\s，。,；;]*", " ", txt)
    txt = re.sub(r"\s{2,}", " ", txt).strip(" |")
    return txt.strip()
for n in rows:
    c = (n.content or '').strip()
    s = (n.summary or '').strip()
    dirty = bool(re.search(r"京ICP备|京公网安备|网站维护|©|备案号", c))
    bad_sum = ("无法" in s[:30]) or ("仅包含" in s[:40]) or ("请补充" in s) or ("未涉及" in s)
    overlap = s and c and (s[:120] == c[:120] or s in c)
    if not (dirty or bad_sum or overlap):
        continue
    try:
        date, summary, cover, full = fetch_detail(n.source_url or '', n.title or '')
    except Exception:
        date, summary, cover, full = None, '', '', ''
    changed = False
    if dirty and full:
        n.content = clean_footer(full[:4000])
        changed = True
    if bad_sum or overlap:
        ai = _ai_summary(n.title or '', n.source or '', date or n.publish_time, n.content or full)
        if ai:
            n.summary = ai[:600]
            changed = True
    if changed:
        updated += 1
        print('FIX', n.id, '|', (n.title or '')[:22], '| content=', len(n.content or ''), '| summary=', len(n.summary or ''))
    if updated >= 500:
        db.commit()
        updated = 0
db.commit()
print('TOTAL_FIXED=', updated)
db.close()
'''
b64 = base64.b64encode(REMOTE_PY.encode('utf-8')).decode()
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=900):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
cmd = "echo %s | base64 -d > /tmp/backfill4.py && cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/backfill4.py 2>&1" % b64
print(run(cmd, 900)[:3500])
cli.close()
print("=== DONE ===")
