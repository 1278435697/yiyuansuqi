# -*- coding: utf-8 -*-
"""看清华艺博首页含日期/新闻的结构"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
probe = r'''
import urllib.request, re
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")
h = get("https://www.artmuseum.tsinghua.edu.cn/")
# 找 2026 日期附近 200 字符
for m in re.finditer(r"2026[-/.年]\d{1,2}[-/.月]\d{1,2}", h):
    s = max(0, m.start()-150)
    print(">>>", h[s:m.end()+80].replace("\n"," ").replace("\r","")[:280])
    print("---")
    if m.start() > 60000: break
'''
cmd = f'cat > /tmp/_probe5.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe5.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(30)
print(out.read().decode('utf-8','replace')[:3000])
cli.close()
print('=== DONE ===')
