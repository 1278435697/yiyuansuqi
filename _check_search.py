# -*- coding: utf-8 -*-
"""服务器直调搜索接口排查"""
import paramiko, io, sys, json, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
kw = urllib.parse.quote('唐代女子日常穿什么服饰？')
cmd = "curl -s -H 'Host: 47.93.14.11' 'http://127.0.0.1:8765/api/home/news-search?keyword=" + kw + "&limit=5'"
_, out, _ = cli.exec_command(cmd)
raw = out.read().decode('utf-8', 'replace')
try:
    d = json.loads(raw)
    print('total:', d.get('total'))
    for it in d.get('items', [])[:5]:
        print('-', it['title'][:40], '|', it.get('snippet', '')[:40])
except Exception:
    print('RAW:', raw[:400])
cli.close()
