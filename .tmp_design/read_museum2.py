"""按字节偏移精确读博物馆 chunk 里两处加载文案的上下文，找出装配阶段 await 了什么。"""
f = r'D:\yisu-ai-platform\.tmp_design\museum_src\MuseumView-aROHavN7.js'
t = open(f, encoding='utf-8', errors='replace').read()

for a, b in [(792711 - 900, 792711 + 1500), (723246 - 900, 723246 + 900)]:
    print('=' * 20, a, b)
    print(t[a:b])
    print()
