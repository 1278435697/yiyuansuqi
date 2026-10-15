# -*- coding: utf-8 -*-
"""解析清华艺博+上博新闻条目（标题/日期/链接/服饰相关）"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
probe = r'''
import urllib.request, re, html as htm
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept":"text/html"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")

# 清华艺博：找新闻/资讯区块
h = get("https://www.artmuseum.tsinghua.edu.cn/")
# 找日期+链接成对
pairs = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*(?:<[^>]+>\s*)*([0-9]{4}[-/.][0-9]{1,2}[-/.][0-9]{1,2})', h)
if not pairs:
    # 日期在链接前
    pairs = re.findall(r'([0-9]{4}[-/.][0-9]{1,2}[-/.][0-9]{1,2})[^<]*</span>[^<]*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h)
print("清华艺博pairs:", len(pairs))
for d, u, t in pairs[:20]:
    t = htm.unescape(re.sub(r"<[^>]+>", "", t)).strip()
    print("  ", d[:10], "|", t[:32], "|", u[:60])

print("---上博---")
h2 = get("https://www.shanghaimuseum.net/")
# 找带日期的链接
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]{4,50})"[^>]*>', h2)
print("上博links:", len(links))
seen = set()
for u, t in links:
    if u in seen: continue
    seen.add(u)
    if any(k in t for k in ["展","服","丝","织","绣","衣","文物","非遗"]):
        print("  ", t[:34], "|", u[:70])
'''
cmd = f'cat > /tmp/_probe4.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe4.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(40)
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
