# -*- coding: utf-8 -*-
import io, sys, paramiko, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(r"D:\yisu-ai-platform\backend\app\api\ai_qa.py","/www/wwwroot/yisu/backend/app/api/ai_qa.py")
sftp.put(r"D:\yisu-ai-platform\backend\app\ai_engine\llm_client.py","/www/wwwroot/yisu/backend/app/ai_engine/llm_client.py")
sftp.put(r"D:\yisu-ai-platform\backend\app\ai_engine\graphrag_engine.py","/www/wwwroot/yisu/backend/app/ai_engine/graphrag_engine.py")
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
run("systemctl restart yisu-backend"); time.sleep(5)
print("active:", run("systemctl is-active yisu-backend"))
# 测 SSE
import requests
r = requests.post("http://127.0.0.1:8000/api/aiqa/chat/stream",
                 json={"question":"深衣是什么","history":[]}, stream=True, timeout=60)
chunks=0
for line in r.iter_lines():
    if line and line.startswith(b"data:"):
        chunks+=1
        if chunks<=3: print("SSE:", line[:120])
    if chunks>20: break
print("total chunks:", chunks)
cli.close()
