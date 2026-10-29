# -*- coding: utf-8 -*-
import json, re, io

src = r"C:\Users\lenovo\Desktop\衣溯AI纹样库_Vue集成包\src\data\patterns-data.js"
s = io.open(src, encoding="utf-8").read()
s = re.sub(r"^//.*$", "", s, flags=re.M)          # 去注释
s = s.replace("export const patternsData = ", "").strip().rstrip(";")
d = json.loads(s)
print("count =", len(d))
print("keys =", list(d[0].keys()))
out = r"D:\yisu-ai-platform\_patterns_full.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
print("saved ->", out)
# 统计服饰应用部位空值
empty_applied = [p for p in d if not (p.get("服饰应用部位") or "").strip()]
print("empty_applied =", len(empty_applied))
