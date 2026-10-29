# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
path = "/www/server/panel/vhost/nginx/yisu.conf"
with sftp.open(path, "r") as f:
    content = f.read().decode("utf-8")
if "chat/stream" not in content:
    block = """    # SSE 流式问答：关闭代理缓冲
    location /api/aiqa/chat/stream {
        proxy_pass http://127.0.0.1:8765/api/aiqa/chat/stream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        chunked_transfer_encoding on;
    }

    location /api/ {"""
    content = content.replace("    location /api/ {", block, 1)
    with sftp.open(path, "w") as f:
        f.write(content)
    print("WRITTEN")
else:
    print("ALREADY")
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
print(run("nginx -t 2>&1 && nginx -s reload 2>&1 && echo RELOADED"))
cli.close()
