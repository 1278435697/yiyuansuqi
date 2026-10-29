"""在压缩后的博物馆 chunk 里定位「正在装配通史馆展品」这一步，看它前后各 await 了什么。"""
import re

f = r'D:\yisu-ai-platform\.tmp_design\museum_src\MuseumView-aROHavN7.js'
t = open(f, encoding='utf-8', errors='replace').read()

for kw in ['通史馆展品', '展品（共', '正在构建', 'buildExhibits', 'loadAsync', 'TextureLoader', 'Promise.all', 'onProgress', '进度']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    print(f'{kw:18s} {len(idxs)} 次  {idxs[:6]}')

i = t.find('通史馆展品')
print('\n===== 上下文（前后 1800 字）=====')
print(t[max(0, i - 1800):i + 1800])
