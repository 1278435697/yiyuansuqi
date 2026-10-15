# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
py = "import sys,logging;logging.disable(logging.CRITICAL);sys.path.insert(0,'.');from sqlalchemy import text;from app.db.database import SessionLocal;db=SessionLocal();sql='''SELECT id, substr(title,1,32) t, substr(source_url,1,45) u FROM news WHERE title LIKE '%珠宝%' OR title LIKE '%钻石%' OR title LIKE '%施华洛%' OR source_url LIKE '%lukfook%' OR source_url LIKE '%swarovski%' OR source_url LIKE '%louisvuitton%' ''';rows=db.execute(text(sql)).all();print('MATCH=',len(rows));[print(r.id,'|',r.t,'|',r.u) for r in rows];db.close()"
cmd = "cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c \"" + py + "\" 2>&1"
print(run(cmd)[:1500])
cli.close()
print("=== DONE ===")
