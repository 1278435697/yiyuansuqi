# -*- coding: utf-8 -*-
"""探测丝博栏目 + 故宫近期服饰相关动态"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
probe = r'''
import urllib.request, re
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")

for name, url in [("丝路进校园","https://www.chinasilkmuseum.com/sljxy/list_291.aspx"),
                  ("国际丝绸学院","https://www.chinasilkmuseum.com/gjscxy/list_307.aspx"),
                  ("服装设计专委会","https://www.chinasilkmuseum.com/bxfzzwh/list_306.aspx"),
                  ("国际丝路中心","https://www.chinasilkmuseum.com/gjslzx/list_305.aspx")]:
    try:
        h = get(url)
        items = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{5,50})</a>', h)
        items = [it for it in items if "list_" not in it[0] and len(it[1].strip())>6][:8]
        dates = re.findall(r"20\d\d[-/.]\d{1,2}[-/.]\d{1,2}", h)[:4]
        print(f"OK {name}: len={len(h)} dates={dates}")
        for u,t in items[:5]:
            print("   ", t.strip()[:28], "|", u[:60])
    except Exception as e:
        print(f"FAIL {name}: {str(e)[:60]}")

print("=== 故宫近期含服饰词动态 ===")
try:
    h2 = get("https://www.dpm.org.cn/about/dynamic.html")
    # 动态条目: 标题+日期配对（故宫结构：<li><a>标题</a><span>日期</span> 或相反）
    seg = re.findall(r'<li[^>]*>(.*?)</li>', h2, re.S)[:40]
    dress = ["服","衣","袍","裙","裳","冠","绣","织","丝","绸","锦","罗","缎","缂","汉服","衣冠"]
    for s in seg:
        t = re.search(r'>([^<>]{4,40})</a>', s)
        d = re.search(r"20\d\d年\d{1,2}月\d{1,2}日", s)
        if t and d:
            tt = t.group(1).strip()
            if any(k in tt for k in dress):
                print("  服饰:", d.group(0), "|", tt[:36])
    # 也输出最近3条全部标题看结构
    n = 0
    for s in seg:
        t = re.search(r'>([^<>]{4,40})</a>', s)
        d = re.search(r"20\d\d年\d{1,2}月\d{1,2}日", s)
        if t and d and n < 6:
            print("  最近:", d.group(0), "|", t.group(1).strip()[:36])
            n += 1
except Exception as e:
    print("FAIL 故宫", str(e)[:60])
'''
cmd = f'cat > /tmp/_probe7.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe7.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(40)
print(out.read().decode('utf-8','replace')[:2800])
cli.close()
print('=== DONE ===')
