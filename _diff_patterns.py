# -*- coding: utf-8 -*-
"""对比 patterns_full.json 与 DB，生成补全 SQL"""
import json, io, paramiko

js = json.load(io.open(r"D:\yisu-ai-platform\_patterns_full.json", encoding="utf-8"))
js_by_name = {}
for p in js:
    name = (p.get("纹样名称") or "").strip()
    if name and name not in js_by_name:
        js_by_name[name] = p
print("js names =", len(js_by_name))

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = "mysql -uroot -phan050607 yisu_ai -N -e 'SELECT id, code, name, IFNULL(applied,\"\"), IFNULL(images,\"[]\") FROM pattern_library WHERE created_by=0 ORDER BY code;' 2>/dev/null"
stdin, stdout, stderr = c.exec_command(cmd)
rows = stdout.read().decode("utf-8", "replace").strip().splitlines()
print("db rows =", len(rows))

def esc(v):
    return str(v).replace("\\", "\\\\").replace("'", "''")

updates_applied = []
updates_images = []
matched = 0
no_js = []
for line in rows:
    parts = line.split("\t")
    if len(parts) < 5:
        continue
    db_id, code, name, applied, images = parts[0], parts[1], parts[2], parts[3], parts[4]
    jp = js_by_name.get(name)
    if jp is None:
        no_js.append(f"{code}:{name}")
        continue
    matched += 1
    js_applied = (jp.get("服饰应用部位") or "").strip()
    if js_applied and not applied.strip():
        updates_applied.append((db_id, js_applied, name))
    js_imgs = jp.get("实物文物图") or []
    db_imgs = []
    try:
        db_imgs = json.loads(images) if images else []
    except Exception:
        db_imgs = []
    if js_imgs and not db_imgs:
        updates_images.append((db_id, json.dumps(js_imgs, ensure_ascii=False), name))

print("matched =", matched)
print("no_js =", len(no_js), no_js[:10])
print("补 applied 条数 =", len(updates_applied))
print("补 images 条数 =", len(updates_images))
print("样例 applied:", [(n, a[:20]) for _, a, n in updates_applied[:5]])
print("样例 images:", [(n, len(json.loads(im))) for _, im, n in updates_images[:5]])

sql_lines = []
for db_id, val, name in updates_applied:
    sql_lines.append(f"UPDATE pattern_library SET applied='{esc(val)}' WHERE id={db_id};")
for db_id, imjson, name in updates_images:
    sql_lines.append(f"UPDATE pattern_library SET images='{esc(imjson)}' WHERE id={db_id};")
with io.open(r"D:\yisu-ai-platform\_patch_patterns.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))
print("SQL written:", len(sql_lines), "statements")
c.close()
