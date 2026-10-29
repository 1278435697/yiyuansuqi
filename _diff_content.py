# -*- coding: utf-8 -*-
"""内容级对比：DB 各字段 vs JS 数据，找出 DB 比 JS 少/缺的"""
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
       "IFNULL(dynasty,\"\"), IFNULL(meaning,\"\"), IFNULL(dynasties,\"[]\"), "
       "IFNULL(meanings,\"[]\"), IFNULL(props,\"{}\"), IFNULL(pairs,\"[]\"), IFNULL(applied,\"\"), "
       "IFNULL(images,\"[]\") FROM pattern_library WHERE created_by=0 ORDER BY code;' 2>/dev/null")
stdin, stdout, stderr = c.exec_command(cmd)
rows = stdout.read().decode("utf-8", "replace").strip().splitlines()
print("db rows =", len(rows))

diffs = {k: [] for k in ["dynasty", "meaning", "dynasties", "meanings", "props", "pairs", "applied", "images"]}
exact_same = 0
for line in rows:
    parts = line.split("\t")
    if len(parts) < 11:
        continue
    db_id, code, name = parts[0], parts[1], parts[2]
    db_dynasty, db_meaning = parts[3], parts[4]
    db_dynasties, db_meanings, db_props, db_pairs, db_applied, db_images = parts[5], parts[6], parts[7], parts[8], parts[9], parts[10]
    jp = js_by_name.get(name)
    if jp is None:
        continue
    j_dynasty = jp.get("盛行朝代") or ""
    j_meaning = jp.get("文化寓意") or ""
    j_dynasties = json.dumps(jp.get("朝代脉络") or [], ensure_ascii=False)
    j_meanings = json.dumps(jp.get("寓意分条") or [], ensure_ascii=False)
    j_props = json.dumps(jp.get("属性") or {}, ensure_ascii=False)
    j_pairs = json.dumps(jp.get("常见搭配") or [], ensure_ascii=False)
    j_applied = jp.get("服饰应用部位") or ""
    j_images = json.dumps(jp.get("实物文物图") or [], ensure_ascii=False)

    def norm(x):
        try:
            return json.dumps(json.loads(x), ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(x).strip()
    checks = [("dynasty", db_dynasty.strip(), j_dynasty.strip()),
              ("meaning", db_meaning.strip(), j_meaning.strip()),
              ("dynasties", norm(db_dynasties), norm(j_dynasties)),
              ("meanings", norm(db_meanings), norm(j_meanings)),
              ("props", norm(db_props), norm(j_props)),
              ("pairs", norm(db_pairs), norm(j_pairs)),
              ("applied", db_applied.strip(), j_applied.strip()),
              ("images", norm(db_images), norm(j_images))]
    if all(a == b for _, a, b in checks):
        exact_same += 1
        continue
    for k, a, b in checks:
        if a != b:
            diffs[k].append((code, name, a[:20], b[:20]))

print("exact_same =", exact_same)
for k, lst in diffs.items():
    print(f"[{k}] 差异 {len(lst)} 条")
    for code, name, a, b in lst[:6]:
        print("   ", code, name, "| DB:", a, "| JS:", b)
c.close()
