# -*- coding: utf-8 -*-
"""验证31种简介无渊源尾巴"""
import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
req = urllib.request.Request('http://47.93.14.11/api/fabrics/list', headers={'Host': '47.93.14.11'})
d = json.load(urllib.request.urlopen(req, timeout=30))
items = d.get('items', [])
bad = 0
for i in items:
    desc = i.get('description', '')
    has_yuan = '〔渊源' in desc
    if has_yuan:
        bad += 1
    print(i['name'], '| len=', len(desc), '| 渊源残留=' + ('Y' if has_yuan else 'N'), '|', desc[:48] + ('…' if len(desc) > 48 else ''))
print('total', len(items), 'bad', bad)
