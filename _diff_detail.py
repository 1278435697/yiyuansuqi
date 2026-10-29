# -*- coding: utf-8 -*-
"""细化 pairs/props 差异：DB 缺失方向"""
import json, io, paramiko

js = json.load(io.open(r"D:\yisu-ai-platform\_patterns_full.json", encoding="utf-8"))
js_by_name = {}
for p in js:
    name = (p.get("纹样名称") or "").strip()
    if name and name not in js_by_name:
        js_by_name[name] = p

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = ("mysql -uroot -phan050607 yisu_ai -N -e 'SELECT id, code, name, "
       "IFNULL(props,\"{}\"), IFNULL(pairs,\"[]\"), IFNULL(applied,\"\") FROM pattern_library "
       "WHERE created_by=0 ORDER BY code;' 2>/dev/null")
stdin, stdout, stderr = c.exec_command(cmd)
rows = stdout.read().decode("utf-8", "replace").strip().splitlines()

pair_missing = []   # DB 缺 JS 中的搭配
pair_extra = []     # DB 有 JS 没有（保留 DB 即可）
pair_order = []     # 仅顺序/表述差异
props_scene_missing = []  # DB props 无"使用场景"键但 JS 有
applied_missing = []
for line in rows:
    parts = line.split("\t")
    if len(parts) < 6:
        if line.strip():
            print("SKIP SHORT LINE:", line[:80])
        continue
    db_id, code, name = parts[0], parts[1], parts[2]
    db_props, db_pairs, db_applied = parts[3], parts[4], parts[5]
    jp = js_by_name.get(name)
    if jp is None:
        continue
    try:
        dp = json.loads(db_props) if db_props else {}
    except Exception:
        dp = {}
    try:
        dl = json.loads(db_pairs) if db_pairs else []
    except Exception:
        dl = []
    jl = jp.get("常见搭配") or []
    js_applied = (jp.get("服饰应用部位") or "").strip()
    jp_scene = (jp.get("属性") or {}).get("使用场景", "")
    if js_applied and not (db_applied or "").strip():
        applied_missing.append((code, name, js_applied))
    if jp_scene and "使用场景" not in dp:
        props_scene_missing.append((code, name, jp_scene))
    if len(jl) != len(dl):
        missing = [x for x in jl if x not in dl]
        extra = [x for x in dl if x not in jl]
        if missing:
            pair_missing.append((code, name, missing, extra))
        elif extra:
            pair_extra.append((code, name, extra))
        else:
            pair_order.append((code, name))
    else:
        if dl != jl:
            pair_order.append((code, name))

print("pairs: 缺 JS 搭配 =", len(pair_missing), "| DB 独有 =", len(pair_extra), "| 仅顺序/表述 =", len(pair_order))
for code, name, miss, extra in pair_missing[:10]:
    print("  MISS", code, name, "缺:", miss, "| DB独有:", extra)
print("props 无使用场景但 JS 有 =", len(props_scene_missing))
for code, name, s in props_scene_missing[:6]:
    print("  ", code, name, "->", s[:40])
print("applied 缺失 =", len(applied_missing), applied_missing)
c.close()
