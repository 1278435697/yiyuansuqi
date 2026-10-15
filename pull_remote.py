# -*- coding: utf-8 -*-
# 反向同步：把云端独有的运维/一次性脚本拉回本地 backend 根目录
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL_BACKEND = r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend"
REMOTE_BACKEND = "/www/wwwroot/yisu/backend"
FILES = ["align_schema.py", "_backfill_questions_to_posts.py", "_backfill_reclassify_posts.py",
         "seed_fix.py", "keepalive.py", "_smoke_demo.py", "_smoke.py"]

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
for f in FILES:
    rp = REMOTE_BACKEND + "/" + f
    lp = os.path.join(LOCAL_BACKEND, f)
    try:
        sftp.get(rp, lp)
        print("pulled:", f, os.path.getsize(lp))
    except Exception as e:
        print("skip:", f, e)
sftp.close()
cli.close()
print("=== DONE ===")
