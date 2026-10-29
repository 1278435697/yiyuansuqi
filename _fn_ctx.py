# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
def decode_unicode(s):
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1),16)), s)
f = "index-BqJJw04H.js"
raw = open(rf"D:\yisu-ai-platform\_dl\{f}", encoding='utf-8', errors='replace').read()
txt = decode_unicode(raw)
# r 函数定义上下文（在 101617 之前找函数体起点）
seg = txt[101300:101760]
print("=== r 函数体 ===")
print(seg)
