# -*- coding: utf-8 -*-
"""从面料工艺素材包 fabrics.json 生成后端 craft_profiles.py"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'C:\Users\lenovo\xwechat_files\wxid_alcxihtea8v922_7624\msg\file\2026-10\面料工艺素材包\fabrics.json'
DST = r'C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\craft_profiles.py'

d = json.load(open(SRC, encoding='utf-8'))
lines = []
lines.append('# -*- coding: utf-8 -*-')
lines.append('"""面料工艺素材（fabrics.json 导入版）：分步制作流程 / 工艺示意图 / 史料依据"""')
lines.append('')
lines.append('CRAFT_MAP = {')
for x in d:
    name = x['name']
    steps = [{'num': s['num'], 'num_cn': s['num_cn'], 'label': s['label'],
              'title': s.get('title', ''), 'desc': s.get('desc', '')}
             for s in x.get('steps', [])]
    images = x.get('images', {})
    note = x.get('history_note', '')
    lines.append('    %s: {' % json.dumps(name, ensure_ascii=False))
    lines.append('        "steps": %s,' % json.dumps(steps, ensure_ascii=False))
    lines.append('        "images": %s,' % json.dumps(images, ensure_ascii=False))
    lines.append('        "history_note": %s,' % json.dumps(note, ensure_ascii=False))
    lines.append('    },')
lines.append('}')
lines.append('')
lines.append('# 数据库面料名 → 素材名 别名映射（库内名称与素材包名称不一致时）')
lines.append('NAME_ALIAS = {"兽皮毛皮": "兽皮"}')
lines.append('')
src = '\n'.join(lines)
open(DST, 'w', encoding='utf-8', newline='\n').write(src)
print('written', len(src), 'chars,', len(d), 'entries ->', DST)
