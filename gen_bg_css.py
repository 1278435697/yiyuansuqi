# -*- coding: utf-8 -*-
"""企业级背景：纯净米白 + 顶部织金'衣缘'镶边（深棕金线回纹）+ 全屏极淡织锦暗纹 + 丝绸光泽"""
import io, sys, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def svg_uri(svg):
    return "url(\"data:image/svg+xml," + urllib.parse.quote(svg, safe="") + "\")"

# 1) 顶部衣缘饰带内的织金回纹（repeat-x，置于深棕带之上）
hui = svg_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="34">'
    '<g fill="none" stroke="#d4a94f" stroke-width="1.3" stroke-linecap="round" opacity="0.65">'
    '<path d="M8 26 h16 v-14 h-9 M38 26 h16 v-14 h-9 M68 26 h16 v-14 h-9 M98 26 h16 v-14 h-9 M128 26 h16 v-14 h-9 M158 26 h14 v-14"/>'
    '<path d="M8 12 h7 M38 12 h7 M68 12 h7 M98 12 h7 M128 12 h7 M158 12 h6"/>'
    '<circle cx="25" cy="26" r="1.6" fill="#d4a94f" stroke="none"/>'
    '<circle cx="55" cy="26" r="1.6" fill="#d4a94f" stroke="none"/>'
    '<circle cx="85" cy="26" r="1.6" fill="#d4a94f" stroke="none"/>'
    '<circle cx="115" cy="26" r="1.6" fill="#d4a94f" stroke="none"/>'
    '<circle cx="145" cy="26" r="1.6" fill="#d4a94f" stroke="none"/>'
    '</g></svg>'
)

# 2) 全屏极淡织锦暗纹（repeat，菱形+圆点，几乎隐形显质感）
anwen = svg_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140">'
    '<g fill="none" stroke="#b98a2f" stroke-width="1">'
    '<path d="M42 42 h56 v56 h-56 z" opacity="0.16"/>'
    '<circle cx="70" cy="70" r="14" opacity="0.12"/>'
    '<path d="M70 34 v72 M34 70 h72" opacity="0.10"/>'
    '<circle cx="0" cy="0" r="3" opacity="0.14"/>'
    '<circle cx="140" cy="0" r="3" opacity="0.14"/>'
    '<circle cx="0" cy="140" r="3" opacity="0.14"/>'
    '<circle cx="140" cy="140" r="3" opacity="0.14"/>'
    '</g></svg>'
)

css_block = f"""body {{
  margin: 0;
  background:
    {hui} repeat-x 0 20px / 180px 34px,
    linear-gradient(180deg, rgba(124, 86, 42, 0.15) 0%, rgba(124, 86, 42, 0.05) 62%, rgba(124, 86, 42, 0) 100%) no-repeat 0 0 / 100% 120px,
    {anwen} repeat,
    linear-gradient(180deg, #fdfaf2 0%, #f8f2e3 46%, #f2ebd7 100%);
  background-attachment: fixed, fixed, fixed, fixed;
  color: var(--ys-ink);
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif;
  -webkit-font-smoothing: antialiased;
}}"""

css_path = r"C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\src\assets\styles\theme.css"
with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

start = content.index("body {")
end = content.index("}", content.index("-webkit-font-smoothing")) + 1
new_content = content[:start] + css_block + content[end:]

with open(css_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("=== theme.css 已更新（企业级·衣缘镶边版）===")
