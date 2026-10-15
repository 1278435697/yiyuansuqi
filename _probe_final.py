# -*- coding: utf-8 -*-
"""探测丝博首页动态 + 故宫动态列表日期"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
probe = r'''
import urllib.request, re
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")

print("=== 丝博首页动态 ===")
try:
    h = get("https://www.chinasilkmuseum.com/")
    # 找新闻动态区标题+日期
    items = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{5,50})</a>', h)
    items = [it for it in items if any(k in it[1] for k in ["展","丝","服","织","绣","衣","馆","活动","工作坊","讲堂"])][:10]
    for u,t in items[:8]:
        print("  ", t.strip()[:30], "|", u[:60])
    dates = re.findall(r"20\d\d[-/.]\d{1,2}[-/.]\d{1,2}", h)[:5]
    print("  日期:", dates)
except Exception as e:
    print("  FAIL", str(e)[:60])

print("=== 故宫动态列表 ===")
try:
    h2 = get("https://www.dpm.org.cn/about/dynamic.html")
    items2 = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{5,50})</a>', h2)
    d2 = re.findall(r"(20\d\d年\d{1,2}月\d{1,2}日)", h2)[:6]
    print("  日期样本:", d2)
    for u,t in items2[:10]:
        print("  ", t.strip()[:32], "|", u[:55])
except Exception as e:
    print("  FAIL", str(e)[:60])
'''
cmd = f'cat > /tmp/_probe6.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe6.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(30)
print(out.read().decode('utf-8','replace')[:2500])
cli.close()
print('=== DONE ===')
