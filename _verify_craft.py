# -*- coding: utf-8 -*-
"""验证后端 craft 字段返回"""
import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
req = urllib.request.Request('http://47.93.14.11/api/fabrics/list', headers={'Host': '47.93.14.11'})
d = json.load(urllib.request.urlopen(req, timeout=30))
items = d.get('items', [])
print('total:', len(items))
with_craft = 0
for i in items:
    c = i.get('craft')
    ok = bool(c and c.get('steps'))
    if ok:
        with_craft += 1
    print(i['name'], 'craft=' + ('Y' if ok else '-'), 'steps=' + (str(len(c['steps'])) if ok else '-'))
print('with_craft:', with_craft, '/', len(items))
