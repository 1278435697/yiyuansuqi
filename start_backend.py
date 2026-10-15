# -*- coding: utf-8 -*-
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=20)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    print('$', c); print(o.read().decode('utf-8','replace'))
    er=e.read().decode('utf-8','replace')
    if er.strip(): print('[err]', er.strip())

V = "/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3"
run(f"{V} -c \"import fastapi, uvicorn, pymysql, sqlalchemy, pydantic_settings; print('DEPS OK')\"")
run("cd /www/wwwroot/yisu/backend && nohup ./591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > logs/uvicorn.log 2>&1 & echo PID=$!")
time.sleep(18)
run("curl -s -m 5 http://127.0.0.1:8765/health || echo CURL_FAIL")
run("tail -40 /www/wwwroot/yisu/backend/logs/uvicorn.log")
cli.close()
print("=== DONE ===")
