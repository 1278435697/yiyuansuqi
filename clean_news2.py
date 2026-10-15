# -*- coding: utf-8 -*-
# 清理词典/游戏/品牌官网/文库等非资讯新闻 + 查看不明来源
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
# 先看不明来源标题
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from app.db.database import SessionLocal
from app.db.models import News
db=SessionLocal()
for n in db.query(News).filter((News.source_url=='')|(News.source_url.like('39.96.62.174%'))|(News.source_url.like('%tcpc.org.cn%'))).all():
    print(n.id, '|', n.source, '|', n.title[:40], '|', n.source_url[:60])
db.close()
" 2>&1""")[:1200])
# 清理
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from app.db.database import SessionLocal
from app.db.models import News
db=SessionLocal()
doms = ('ds.163.com','chagushici.com','gushici.net','hanyuguoxue.com','wenku.baidu.com','zgbk.com','hm.com.cn','uniqlo.cn','meikansocks.com','sheygo.com')
from sqlalchemy import or_
cond = or_(*[News.source_url.like('%'+d+'%') for d in doms]) | or_(*[News.title.contains(w) for w in ('怎么读','的意思','字典','词典','攻略','副本','拼音','读音','文库','古诗')])
q=db.query(News).filter(cond)
print('to_delete=', q.count())
q.delete(synchronize_session=False); db.commit()
print('deleted')
db.close()
" 2>&1""")[:400])
cli.close()
print("=== DONE ===")
