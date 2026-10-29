# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
def decode_unicode(s):
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1),16)), s)
def ctx(txt, start, width=120):
    return txt[max(0,start-60):start+width].replace("\n"," ")

f = "index-BqJJw04H.js"
raw = open(rf"D:\yisu-ai-platform\_dl\{f}", encoding='utf-8', errors='replace').read()
txt = decode_unicode(raw)
print("=== index 品牌区 ===")
for i in [101748, 101766, 101881, 101888, 102043, 102251, 102230, 101617]:
    print("---", i, ":", ctx(txt, i))

f2 = "MuseumView-aROHavN7.js"
raw2 = open(rf"D:\yisu-ai-platform\_dl\{f2}", encoding='utf-8', errors='replace').read()
txt2 = decode_unicode(raw2)
print("\n=== MuseumView 品牌上下文（前6处）===")
for i in [358, 387, 137945, 138516, 139068, 139576]:
    print("---", i, ":", ctx(txt2, i))
