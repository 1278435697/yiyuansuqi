# -*- coding: utf-8 -*-
"""查看 3 条待补纹样的 DB/JS 完整值"""
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
       "WHERE code IN (26,220,243);' 2>/dev/null")
stdin, stdout, stderr = c.exec_command(cmd)
rows = stdout.read().decode("utf-8", "replace").strip().splitlines()
for line in rows:
    parts = line.split("\t")
    if len(parts) < 6:
        continue
    print("=== DB", parts[0], parts[1], parts[2])
    print("  props:", parts[3])
    print("  pairs:", parts[4])
    print("  applied:", repr(parts[5]))
    jp = js_by_name.get(parts[2])
    if jp:
        print("  JS pairs:", json.dumps(jp.get("常见搭配") or [], ensure_ascii=False))
        print("  JS props:", json.dumps(jp.get("属性") or {}, ensure_ascii=False))
        print("  JS applied:", repr(jp.get("服饰应用部位") or ""))
c.close()
