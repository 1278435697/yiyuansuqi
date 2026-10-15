# -*- coding: utf-8 -*-
import paramiko, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REMOTE_PY = r'''import sys, logging; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
from sqlalchemy import text
from app.db.database import SessionLocal
db=SessionLocal()
sql = """SELECT id, substr(title,1,36) t, substr(source_url,1,50) u FROM news WHERE
 source_url LIKE '%ds.163.com%' OR source_url LIKE '%chagushici%' OR source_url LIKE '%gushici.net%'
 OR source_url LIKE '%hanyuguoxue%' OR source_url LIKE '%wenku.baidu%' OR source_url LIKE '%zgbk.com%'
 OR source_url LIKE '%hm.com.cn%' OR source_url LIKE '%uniqlo%' OR source_url LIKE '%meikansocks%'
 OR source_url LIKE '%sheygo%' OR title LIKE '%怎么读%' OR title LIKE '%的意思%'
 OR title LIKE '%字典%' OR title LIKE '%词典%' OR title LIKE '%攻略%' OR title LIKE '%副本%'
 OR title LIKE '%拼音%' OR title LIKE '%读音%' OR title LIKE '%文库%'"""
rows = db.execute(text(sql)).all()
print('MATCH=', len(rows))
for r in rows:
    print(r.id, '|', r.t, '|', r.u)
db.close()
'''
b64 = base64.b64encode(REMOTE_PY.encode('utf-8')).decode()
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
cmd = "echo %s | base64 -d > /tmp/diag_news.py && cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/diag_news.py 2>&1" % b64
print(run(cmd)[:3000])
cli.close()
print("=== DONE ===")
