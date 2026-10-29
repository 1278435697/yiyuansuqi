import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = (
    "pkill -f 'uvicorn app.main:app'; sleep 2; "
    "cd /www/wwwroot/yisu/backend && "
    "nohup /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/uvicorn.log 2>&1 & echo RESTARTED"
)
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
c.close()
