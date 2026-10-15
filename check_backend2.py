# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print("== home.py 是否含过滤 ==")
print(run("grep -n '_dress_ok\\|DRESS_WORDS' /www/wwwroot/yisu/backend/app/api/home.py | head -10") or "(none)")
print("== news_fetcher 新词表检查 ==")
print(run("grep -n '\\\"织\\\",' /www/wwwroot/yisu/backend/app/ai_engine/news_fetcher.py | head -3") or "(单字织已移除 OK)")
print("== 接口 items 前几条 ==")
print(run("curl -s -m 10 'http://127.0.0.1:8765/api/home/news?page_size=10' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('FOCUS:', [x['title'][:30] for x in d['focus']]); print('ITEMS:', [x['title'][:30] for x in d['items']])\" 2>&1")[:1000])
cli.close()
print("=== DONE ===")
