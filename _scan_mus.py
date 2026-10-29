# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
def decode_unicode(s):
    # 解码 \uXXXX 转义（保留字面反斜杠）
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1),16)), s)
for f in ["index-BqJJw04H.js", "MuseumView-aROHavN7.js", "TryonPlaceholder-Bp1Rhoms.js"]:
    print("==========", f)
    raw = open(rf"D:\yisu-ai-platform\_dl\{f}", encoding='utf-8', errors='replace').read()
    txt = decode_unicode(raw)
    for kw in ["衣溯AI", "华夏衣冠志", "数字博物馆", "返回主站", "博物馆展厅", "on:{click", "onClick", "href:\"/\"", "href=\"/\"", "华夏服饰溯源与复原平台", "衣溯"]:
        idxs = [m.start() for m in re.finditer(re.escape(kw), txt)]
        if idxs:
            print(f"  [{kw}] x{len(idxs)}: " + "; ".join(str(i) for i in idxs[:8]))
