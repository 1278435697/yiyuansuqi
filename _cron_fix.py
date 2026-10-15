# -*- coding: utf-8 -*-
"""修复 crontab news_fetcher 行为标准 2 小时任务"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
code = r'''
import subprocess
lines = subprocess.run(["crontab","-l"], capture_output=True, text=True).stdout.splitlines()
newline = "0 */2 * * * cd /www/wwwroot/yisu/backend && /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 app/ai_engine/news_fetcher.py >> /tmp/yisu_news_fetch.log 2>&1"
out = []
for l in lines:
    if "news_fetcher.py" in l:
        out.append(newline)
    else:
        out.append(l)
txt = "\n".join(out) + "\n"
subprocess.run(["crontab","-"], input=txt, text=True)
print(subprocess.run(["crontab","-l"], capture_output=True, text=True).stdout)
'''
cmd = f'cat > /tmp/_fixcron.py << "EOF"\n{code}\nEOF\npython3 /tmp/_fixcron.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:300])
cli.close()
print('=== DONE ===')
