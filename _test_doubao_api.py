# -*- coding: utf-8 -*-
"""服务器实测豆包 API 连通性与回答质量"""
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
script = '''
# -*- coding: utf-8 -*-
import requests, json, os
base = os.environ.get("LLM_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
key = os.environ.get("LLM_API_KEY") or ""
# 从 .env 读
for line in open("/www/wwwroot/yisu/backend/.env", encoding="utf-8"):
    line=line.strip()
    if line.startswith("LLM_BASE_URL="): base=line.split("=",1)[1]
    if line.startswith("LLM_API_KEY="): key=line.split("=",1)[1]
    if line.startswith("LLM_MODEL="): model=line.split("=",1)[1]
print("base:", base)
print("model:", model)
print("key_head:", key[:10]+"...")
try:
    r = requests.post(
        base + "/chat/completions",
        headers={"Authorization": "Bearer "+key, "Content-Type": "application/json"},
        json={"model": model, "messages": [
            {"role":"system","content":"你是华夏服饰史考据助手。"},
            {"role":"user","content":"什么是香云纱？请简要介绍。"}
        ], "temperature": 0.4, "max_tokens": 300},
        timeout=60)
    print("HTTP", r.status_code)
    print(r.text[:800])
except Exception as e:
    print("EXC", repr(e))
'''
# 写入服务器并执行
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
with sftp.open('/tmp/test_doubao.py', 'w') as f:
    f.write(script)
sftp.close()
_, out, err = cli.exec_command(f'{PY} /tmp/test_doubao.py')
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace')
if e.strip(): print("STDERR:", e[:500])
cli.close()
