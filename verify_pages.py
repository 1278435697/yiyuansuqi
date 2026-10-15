# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print(run("""cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c "
import sys, logging, json, urllib.request; logging.disable(logging.CRITICAL); sys.path.insert(0,'.')
d=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/home/news?page_size=10&page=1', timeout=10))
print('total=', d['total'])
print('focus:', [x['title'][:24] for x in d['focus']])
print('p1 :', [x['title'][:20] for x in d['items']])
d2=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/home/news?page_size=10&page=3', timeout=10))
print('p3 count=', len(d2['items']), [x['title'][:16] for x in d2['items'][:3]])
d4=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/home/news?page_size=10&page=7', timeout=10))
print('p7 count=', len(d4['items']))
" 2>&1""")[:1200])
cli.close()
print("=== DONE ===")
