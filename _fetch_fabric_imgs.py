# -*- coding: utf-8 -*-
"""下载新增8种面料的权威文物图到 frontend/public/images/fabrics/"""
import urllib.request, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\public\images\fabrics'
os.makedirs(DIR, exist_ok=True)

IMAGES = [
    ('fabric_shujin.jpg', 'https://aka.doubaocdn.com/s/mu0xfqH8pM', '汉代蜀锦"五星出东方利中国"护臂·新疆博物馆'),
    ('fabric_wan.jpg', 'https://aka.doubaocdn.com/s/y3kOvpIyxb', '战国绢（细密平纹·纨类）·齐文化博物院'),
    ('fabric_jianchou.jpg', 'https://aka.doubaocdn.com/s/wUm6ptpoSR', '清乾隆京酱色程乡茧绸·故宫博物院'),
    ('fabric_chou.jpg', 'https://aka.doubaocdn.com/s/hFR2TLREvZ', '明绸直襬·泰州博物馆(森森村明墓出土)'),
    ('fabric_he.jpg', 'https://aka.doubaocdn.com/s/OElOo3K6DC', '毛布残片(褐类)·青海省博物馆(诺木洪遗址出土)'),
    ('fabric_jiaobu.jpg', 'https://aka.doubaocdn.com/s/LLMAA8xvim', '喜如嘉芭蕉布(蕉布同工艺)·冲绳传统织物'),
    ('fabric_yuduan.jpg', 'https://aka.doubaocdn.com/s/l5TGWMKavO', '清道光大红色羽缎单氅衣·故宫博物院'),
    ('fabric_kuduan.jpg', 'https://aka.doubaocdn.com/s/DDO33h2M9e', '绿地凤穿牡丹纹库金缎·故宫博物院'),
]

ok = []
for fn, url, note in IMAGES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=60).read()
        p = os.path.join(DIR, fn)
        open(p, 'wb').write(data)
        ok.append((fn, len(data)))
        print(fn, len(data), note)
    except Exception as e:
        print(fn, 'FAIL', e)
print('ok', len(ok), '/', len(IMAGES))
