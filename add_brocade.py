# -*- coding: utf-8 -*-
"""在theme.css body背景中加入真实织锦面料层（白膜控制透明度）"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

css_path = r"C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\src\assets\styles\theme.css"
with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

start = content.index("body {")
end = content.index("}", content.index("-webkit-font-smoothing")) + 1
block = content[start:end]

# 在渐变底之前插入 织锦面料 + 白膜 两层
old_tail = "    linear-gradient(115deg, #f2e7d2 0%, #faf3e3 30%, #efe2c8 55%, #f8f0de 78%, #ecdec2 100%);"
new_tail = (
    "    linear-gradient(rgba(248, 243, 232, 0.55), rgba(248, 243, 232, 0.55)),\n"
    "    url(\"/images/bg/bg_brocade.jpg\") center / cover no-repeat fixed,\n"
    "    linear-gradient(115deg, #f2e7d2 0%, #faf3e3 30%, #efe2c8 55%, #f8f0de 78%, #ecdec2 100%);"
)
assert old_tail in block, "渐变尾未找到"
block = block.replace(old_tail, new_tail)

# 更新 background-attachment 列表：原7项(fixed*6+scroll+fixed) → 8项
old_att = "background-attachment: fixed, fixed, fixed, fixed, fixed, fixed, scroll, fixed;"
new_att = "background-attachment: fixed, fixed, fixed, fixed, fixed, fixed, scroll, fixed, fixed;"
assert old_att in block, "attachment行未找到"
block = block.replace(old_att, new_att)

content = content[:start] + block + content[end:]
with open(css_path, "w", encoding="utf-8") as f:
    f.write(content)
print("=== 织锦面料层已加入 ===")
