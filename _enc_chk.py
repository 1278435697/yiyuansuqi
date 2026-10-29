# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for f in ["index-BqJJw04H.js", "MuseumView-aROHavN7.js"]:
    raw = open(rf"D:\yisu-ai-platform\_dl\{f}", "rb").read()
    has_esc = b"\\u8863" in raw  # \u8863 = 衣
    has_lit = "衣溯AI".encode("utf-8") in raw
    print(f, "| escaped_unicode:", has_esc, "| literal_utf8:", has_lit)
