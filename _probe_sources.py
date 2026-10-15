# -*- coding: utf-8 -*-
"""手动跑抓取器 + 探测新源"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
# 1) 手动跑抓取器
_, out, err = cli.exec_command(f"cd /www/wwwroot/yisu/backend && timeout 120 {PY} app/ai_engine/news_fetcher.py 2>&1 | tail -6")
time.sleep(70)
print("FETCH_RUN:")
print(out.read().decode('utf-8','replace'))

# 2) 探测清华艺博资讯页
probe = r'''
import urllib.request, re
def get(u, hdr=None):
    req = urllib.request.Request(u, headers=hdr or {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")
for name, url in [("清华艺博","https://www.artmuseum.tsinghua.edu.cn/cps/uppage/newslist/news_list_9_0_0.html"),
                  ("苏州丝博","http://www.szsilkmuseum.com/news.html")]:
    try:
        h = get(url)
        import re as r
        dates = re.findall(r"20\d\d[-/\.]\d{1,2}[-/\.]\d{1,2}", h)[:3]
        links = re.findall(r'href="([^"]+)"[^>]*>([^<]{6,40})</a>', h)
        links = [l for l in links if "20" in l[1] or "news" in l[0].lower()][:5]
        print(f"{name}: OK len={len(h)} dates={dates}")
        for l in links[:4]:
            print("   ", l[0][:50], "|", l[1].strip()[:30])
    except Exception as e:
        print(f"{name}: FAIL {str(e)[:80]}")
'''
cmd = f'cat > /tmp/_probe2.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe2.py 2>&1'
_, out, err = cli.exec_command(cmd)
time.sleep(20)
print("PROBE:")
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
