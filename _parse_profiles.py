# -*- coding: utf-8 -*-
"""解析 fabric_profiles(1).html → 结构化面料档案 JSON（31种，修正 category/period）"""
import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = r'C:\Users\lenovo\Desktop\fabric_profiles(1).html'
OUT = r'C:\Users\lenovo\Desktop\yisu-ai-platform\_profiles_31.json'

src = open(HTML, encoding='utf-8').read()
blocks = re.split(r'<!--\s*\d+\s*[^>]*?-->', src)

def clean(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n', s)
    return s.strip()

profiles = []
for i, b in enumerate(blocks[1:], 1):
    m = re.search(r'<span[^>]*>\s*(\d+)\.\s*([^<]+)</span>', b)
    if not m:
        print('skip block', i, b[:60]); continue
    name = m.group(2).strip()
    # category：带 background 的 span；period：其后无 background 的 span
    cm = re.search(r'<span style="background:[^"]*"[^>]*>\s*([^<]+?)\s*</span>', b)
    category = cm.group(1).strip() if cm else ''
    pm = re.search(r'<span style="font-size:11px;color:#6B7280;">\s*([^<]+?)\s*</span>', b)
    period = pm.group(1).strip() if pm else ''
    # 面料简介
    dm = re.search(r'<b>面料简介：</b>\s*(.*?)(?=<b>原料：</b>)', b, re.S)
    desc = clean(dm.group(1)) if dm else ''
    rm = re.search(r'<b>原料：</b>\s*(.*?)(?=<b>制作流程：</b>)', b, re.S)
    raw = clean(rm.group(1)) if rm else ''
    # 制作流程
    proc_block = re.search(r'<b>制作流程：</b>(.*?)(?=<b>诗文·古文：</b>)', b, re.S)
    steps = []
    if proc_block:
        items = re.findall(r'<b>([^<]+)</b>\s*(?:<div[^>]*>(.*?)</div>)?', proc_block.group(1), re.S)
        for t, d in items:
            tt = clean(t)
            dd = clean(d) if d else ''
            if tt:
                steps.append({'title': tt, 'desc': dd})
    # 诗文
    poem_block = re.search(r'<b>诗文·古文：</b>(.*?)(?=<div style="font-size:11px|$)', b, re.S)
    poems = []
    if poem_block:
        pitems = re.findall(r'<div[^>]*>\s*(.*?)\s*</div>', poem_block.group(1), re.S)
        for p in pitems:
            a = re.search(r'<a href="([^"]+)"', p)
            url = a.group(1) if a else ''
            txt = clean(re.sub(r'<a[^>]*>.*?</a>', '', p))
            txt = re.sub(r'^\d+[\.\、]?\s*', '', txt).strip()
            if txt:
                poems.append({'text': txt, 'url': url})
    profiles.append({
        'id': i, 'name': name, 'category': category, 'period': period,
        'description': desc, 'raw_material': raw, 'steps': steps, 'poems': poems,
    })
    print(i, name, '|', category, '|', period, '| desc=', len(desc), '| steps=', len(steps), '| poems=', len(poems))

json.dump(profiles, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('TOTAL:', len(profiles))
