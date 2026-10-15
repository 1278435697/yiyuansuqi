# -*- coding: utf-8 -*-
# 上传 community.py + 编译 + 重启 uvicorn
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\community.py",
         "/www/wwwroot/yisu/backend/app/api/community.py")
sftp.close()
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print(run("cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m py_compile app/api/community.py && echo COMPILE_OK"))
print(run("pkill -f 'uvicorn app.main:app' || true; sleep 2; nohup 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 >> /tmp/yisu_uvicorn.log 2>&1 & echo RESTARTED")[:200])
cli.close()
print("=== DONE ===")
