# -*- coding: utf-8 -*-
"""批量探测服饰主题资讯源"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
probe = r'''
import urllib.request, re
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept":"text/html"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")
sites = [
    ("上海博物馆新闻","https://www.shanghaimuseum.net/museum/frontend/articles?categoryId=12"),
    ("上海博物馆首页","https://www.shanghaimuseum.net/"),
    ("南京云锦","http://www.njyunjin.cn/"),
    ("苏州丝博首页","http://www.szsilkmuseum.com/"),
    ("苏州丝博新闻2","http://www.szsilkmuseum.com/a/xinwen/"),
    ("清华艺博首页","https://www.artmuseum.tsinghua.edu.cn/"),
    ("清华艺博展讯","https://www.artmuseum.tsinghua.edu.cn/cps/site/artmuseum/exhibition/list_exhibition_1_1.html"),
    ("中国丝绸博物馆展览","https://www.chinasilkmuseum.com/gjss/list_307.aspx"),
    ("中国丝绸博物馆合作","https://www.chinasilkmuseum.com/gjslzx/list_211.aspx"),
]
for name, url in sites:
    try:
        h = get(url)
        dates = re.findall(r"20\d\d[-/.]\d{1,2}[-/.]\d{1,2}", h)[:3]
        titles = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{6,40})</a>', h)
        t2 = [t for t in titles if any(k in t[1] for k in ["展","服饰","丝绸","汉服","文物","非遗","织","绣","衣"])][:4]
        print(f"OK  {name}: len={len(h)} dates={dates}")
        for l in t2[:3]:
            print("     ", l[0][:55], "|", l[1].strip()[:28])
    except Exception as e:
        print(f"FAIL {name}: {str(e)[:60]}")
'''
cmd = f'cat > /tmp/_probe3.py << "EOF"\n{probe}\nEOF\n{PY} /tmp/_probe3.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(60)
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
