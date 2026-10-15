# -*- coding: utf-8 -*-
"""给库内故宫资讯回填详情页首图 cover_image（本地连服务器库执行）"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

code = r'''
import sys, re, datetime, urllib.request, logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
def get_cover(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "replace")
    except Exception:
        return ""
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', html):
        src = m.group(1)
        if "/Uploads/image/" in src and "static" not in src and "icon" not in src:
            return src
    return ""

db = SessionLocal()
rows = db.query(News).filter(News.source == "故宫博物院", News.cover_image == "").all()
print("待补图:", len(rows))
ok = 0
for n in rows:
    c = get_cover(n.source_url)
    if c:
        n.cover_image = c[:255]
        ok += 1
db.commit()
print("已补图:", ok)
# 输出最新10条带图状态
for x in db.query(News).filter(News.source == "故宫博物院").order_by(News.publish_time.desc(), News.id.desc()).limit(10).all():
    print("  -", x.publish_time.date() if x.publish_time else "?", x.title[:20], "img=" + ("Y" if x.cover_image else "N"))
db.close()
'''
cmd = f'cat > /tmp/_backfill_covers.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_backfill_covers.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(25)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
