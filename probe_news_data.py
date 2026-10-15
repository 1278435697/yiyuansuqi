# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
# 有效服饰新闻总数（走过滤逻辑）
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from app.db.database import SessionLocal
from app.db.models import News
from app.ai_engine.news_fetcher import dress_match
db=SessionLocal()
all_n=db.query(News).all()
ok=[n for n in all_n if n.source=='中国丝绸博物馆' or dress_match((n.title or '')+(n.summary or ''))]
print('total_db=',len(all_n),'dress_ok=',len(ok))
from collections import Counter
print('src:',dict(Counter(n.source for n in all_n)))
dates=sorted([n.publish_time for n in all_n if n.publish_time])
print('newest=',dates[-1].date() if dates else None,'oldest=',dates[0].date() if dates else None)
db.close()
" 2>&1""")[:800])
# 是否有定时任务
print("== cron ==")
print((run("crontab -l 2>/dev/null | grep -i news") or "(无 news cron)"))
cli.close()
print("=== DONE ===")
