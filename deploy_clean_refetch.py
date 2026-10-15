# -*- coding: utf-8 -*-
# 部署抓取器更新 + 清理百科/电商垃圾新闻 + 重跑抓取
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=600):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

sftp = cli.open_sftp()
sftp.put(r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\ai_engine\news_fetcher.py",
         "/www/wwwroot/yisu/backend/app/ai_engine/news_fetcher.py")
sftp.close()
print("uploaded news_fetcher.py")
print(run("cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m py_compile app/ai_engine/news_fetcher.py && echo COMPILE_OK")[:200])

# 清理百科/电商/问答类非资讯新闻（先备份计数）
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from app.db.database import SessionLocal
from app.db.models import News
db=SessionLocal()
q=db.query(News).filter(
    (News.source_url.like('%baike.baidu.com%')) | (News.source_url.like('%alibaba%')) |
    (News.source_url.like('%1688%')) | (News.source_url.like('%jd.com%')) |
    (News.source_url.like('%tmall%')) | (News.source_url.like('%taobao%')) |
    (News.source_url.like('%zhihu.com%')) | (News.source_url.like('%wikipedia%'))
)
n=q.count(); q.delete(synchronize_session=False); db.commit()
print('deleted_nonnews=', n)
db.close()
" 2>&1""")[:300])

# 重跑抓取
print(run("cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 app/ai_engine/news_fetcher.py 2>&1 | grep -E '\\[fetch\\]|\\[db\\]'", 600)[:800])
cli.close()
print("=== DONE ===")
