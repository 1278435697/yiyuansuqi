# -*- coding: utf-8 -*-
"""清洗纹样 JSON → patterns_clean.json（321条，去重取优，补旧版5条）"""
import json, os, glob

root = r"C:\Users\lenovo\Desktop\衣溯AI纹样资料库_完整包\shujv"
files = glob.glob(os.path.join(root, "**", "*.json"), recursive=True)

def pick(dup_list):
    """重复对取优：图数多 → 寓意长 → 朝代多"""
    def score(d):
        return (len(d.get("实物文物图", []) or []),
                len(d.get("文化寓意", "") or ""),
                len(d.get("朝代脉络", []) or []))
    return max(dup_list, key=score)

new_by_name = {}
old_list = []
for f in files:
    with open(f, encoding="utf-8") as fp:
        d = json.load(fp)
    if "编号" in d:
        new_by_name.setdefault(d.get("纹样名称"), []).append(d)
    else:
        old_list.append(d)

# 新版去重
new_clean = [pick(v) for v in new_by_name.values()]
new_names = {d.get("纹样名称") for d in new_clean}

# 旧版补缺（跳过与新版同名）
old_keep = [d for d in old_list if d.get("纹样名称") not in new_names]
print("新版保留:", len(new_clean), "| 旧版补入:", len(old_keep))

def norm(d):
    imgs = d.get("实物文物图", []) or []
    imgs = [{"url": i.get("url", ""), "caption": i.get("caption", "")} for i in imgs if i.get("url")]
    return {
        "code": d.get("编号"),
        "name": d.get("纹样名称"),
        "category": d.get("类别") or d.get("分类") or "",
        "seq": d.get("类别内序号"),
        "dynasty": d.get("盛行朝代", "") or "",
        "meaning": d.get("文化寓意", "") or "",
        "images": imgs,
        "dynasties": d.get("朝代脉络", []) or [],
        "meanings": d.get("寓意分条", []) or [],
        "props": d.get("属性", {}) or {},
        "pairs": d.get("常见搭配", []) or [],
        "compose": d.get("体系组成", "") or "",
        "similar": d.get("相似纹样说明", "") or "",
        "applied": d.get("服饰应用部位", "") or "",
    }

all_data = [norm(d) for d in new_clean + old_keep]
# 按 分类 → 序号 排序
all_data.sort(key=lambda x: (x["category"], x["seq"] or 0, x["code"] or 0))

out = r"D:\yisu-ai-platform\backend\patterns_clean.json"
with open(out, "w", encoding="utf-8") as fp:
    json.dump(all_data, fp, ensure_ascii=False, indent=1)
print("输出:", out, "| 总条数:", len(all_data))

# 汇总
from collections import Counter
c = Counter(x["category"] for x in all_data)
for k, v in sorted(c.items()):
    print(f"  {k}: {v}")
img_n = sum(1 for x in all_data if x["images"])
print("带图:", img_n, "| 无图:", len(all_data) - img_n)
