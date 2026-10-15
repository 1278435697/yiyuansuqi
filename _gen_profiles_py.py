# -*- coding: utf-8 -*-
"""由 _profiles_31.json 生成 backend/app/api/fabric_profiles.py（31种，html 内容重建）"""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'C:\Users\lenovo\Desktop\yisu-ai-platform\_profiles_31.json'
DST = r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\fabric_profiles.py'

profiles = json.load(open(SRC, encoding='utf-8'))

def extract_book(text):
    m = re.search(r'《[^》]+》', text)
    return m.group(0) if m else ''

lines = []
lines.append('# -*- coding: utf-8 -*-')
lines.append('"""华夏服饰面料 · 档案（31 种）完整数据：简介 / 原料 / 分步流程 / 诗文古文（含检索链接）')
lines.append('数据来源：用户提供的 fabric_profiles(1).html 方案（31 种）。"""')
lines.append('')
lines.append('')
lines.append('FABRIC_PROFILES = [')
for p in profiles:
    name = p['name']
    desc = p['description']
    raw = p['raw_material']
    period = p['period']
    cat = p['category']
    steps = p['steps']
    poems = p['poems']
    src_ref = extract_book(desc) or '史料见诗文检索'
    lines.append('    {')
    lines.append('        "name": %s,' % json.dumps(name, ensure_ascii=False))
    lines.append('        "category": %s,' % json.dumps(cat, ensure_ascii=False))
    lines.append('        "dynasty_peak": %s,' % json.dumps(period, ensure_ascii=False))
    lines.append('        "raw_material": %s,' % json.dumps(raw, ensure_ascii=False))
    lines.append('        "description": %s,' % json.dumps(desc, ensure_ascii=False))
    lines.append('        "source_ref": %s,' % json.dumps(src_ref, ensure_ascii=False))
    # process 简短摘要串（步骤标题已含①②等前缀，直接串联）
    proc = ' → '.join(s['title'] for s in steps) if steps else ''
    lines.append('        "process": %s,' % json.dumps(proc, ensure_ascii=False))
    # process_steps 结构化
    psteps = [{'title': s['title'], 'desc': s['desc']} for s in steps]
    lines.append('        "process_steps": %s,' % json.dumps(psteps, ensure_ascii=False))
    # poems
    plist = []
    for po in poems:
        txt = po['text']
        plist.append({'text': txt, 'src': extract_book(txt), 'url': po['url']})
    lines.append('        "poems": %s,' % json.dumps(plist, ensure_ascii=False))
    lines.append('    },')
lines.append(']')
lines.append('')
lines.append('FABRIC_PROFILES_MAP = {f["name"]: f for f in FABRIC_PROFILES}')
lines.append('')
src = '\n'.join(lines)
open(DST, 'w', encoding='utf-8', newline='\n').write(src)
print('written', len(src), 'chars,', len(profiles), 'profiles')
