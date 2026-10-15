# -*- coding: utf-8 -*-
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=20)
sftp = cli.open_sftp()
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    print('$', c); print(o.read().decode('utf-8','replace'))
    er=e.read().decode('utf-8','replace')
    if er.strip(): print('[err]', er.strip())

V = "/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3"

# 1) 上传修正后的 config.py
sftp.put(r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\core\config.py",
         "/www/wwwroot/yisu/backend/app/core/config.py")
print("UPLOADED config.py")

# 2) 先杀掉上次残留进程（如果还在）
run("pkill -f 'uvicorn app.main:app' 2>/dev/null; sleep 1; ss -tlnp | grep 8765 || echo '8765 free'")

# 3) 验证 settings 读取
run(f"cd /www/wwwroot/yisu/backend && {V} -c \"from app.core.config import settings; print('CFG_PWD=', settings.MYSQL_PASSWORD, 'HOST=', settings.MYSQL_HOST, 'DB=', settings.MYSQL_DB)\"")

# 4) 启动
run("cd /www/wwwroot/yisu/backend && nohup ./591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > logs/uvicorn.log 2>&1 & echo PID=$!")
time.sleep(20)

# 5) 验证
run("curl -s -m 5 http://127.0.0.1:8765/health || echo CURL_FAIL")
run("curl -s -m 5 http://127.0.0.1:8765/ || head -c 400")
run("tail -25 /www/wwwroot/yisu/backend/logs/uvicorn.log")
sftp.close()
cli.close()
print("=== DONE ===")
