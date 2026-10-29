# -*- coding: utf-8 -*-
import io, sys, paramiko, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c):
    i,o,e = cli.exec_command(c, timeout=30)
    return (o.read().decode('utf-8','replace')+e.read().decode('utf-8','replace')).strip()
# 备份
print(run("cp /www/server/panel/vhost/nginx/yisu.conf /www/server/panel/vhost/nginx/yisu.conf.bak_sse"))
# 在 location /api/ { 前插入 SSE location
new_block = """
    # SSE 流式问答：关闭代理缓冲
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
print(run("sed -i 's|    location /api/ {|" + new_block.replace(chr(92),chr(92)*2).replace(chr(39),chr(92)+chr(39)) + "|' /www/server/panel/vhost/nginx/yisu.conf"))
print("--- check ---")
print(run("grep -n 'stream\\|proxy_buffering' /www/server/panel/vhost/nginx/yisu.conf"))
print("--- test ---")
print(run("nginx -t 2>&1"))
print("--- reload ---")
print(run("nginx -s reload 2>&1"))
cli.close()
