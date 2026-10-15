# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
py = "import sys,logging;logging.disable(logging.CRITICAL);sys.path.insert(0,'.');from app.core.config import settings;print('URI=',settings.SQLALCHEMY_DATABASE_URI);from app.db.database import SessionLocal;db=SessionLocal();print('DB-OK');db.close()"
cmd = "cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c \"" + py + "\" 2>&1"
print(run(cmd)[:2500])
cli.close()
print("=== DONE ===")
