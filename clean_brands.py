# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
py = "import sys,logging;logging.disable(logging.CRITICAL);sys.path.insert(0,'.');from sqlalchemy import text;from app.db.database import SessionLocal;db=SessionLocal();sql='''DELETE FROM news WHERE source_url LIKE '%lukfook%' OR source_url LIKE '%louisvuitton%' OR source_url LIKE '%swarovski%' OR source_url LIKE '%tiffany%' OR source_url LIKE '%cartier%' OR source_url LIKE '%pandora%' OR source_url LIKE '%chowtaifook%' OR source_url LIKE '%chowsangsang%' OR source_url LIKE '%laofengxiang%' OR title LIKE '%官方商城%' OR title LIKE '%珠宝商城%' OR title LIKE '%钻石%' OR title LIKE '%足金%' ''';r=db.execute(text(sql));db.commit();print('DELETED=',r.rowcount);db.close()"
cmd = "cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c \"" + py + "\" 2>&1"
print(run(cmd)[:800])
cli.close()
print("=== DONE ===")
