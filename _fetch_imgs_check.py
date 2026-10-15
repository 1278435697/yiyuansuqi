# -*- coding: utf-8 -*-
"""拉取31种面料image_url并下载到本地待核对"""
import urllib.request, json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

req = urllib.request.Request('http://47.93.14.11/api/fabrics/list', headers={'Host': '47.93.14.11'})
d = json.load(urllib.request.urlopen(req, timeout=30))
items = d.get('items', [])
outdir = r'C:\Users\lenovo\Desktop\yisu-ai-platform\_img_check'
os.makedirs(outdir, exist_ok=True)
manifest = []
for i, it in enumerate(items):
    name = it['name']; img = it.get('image_url', '')
    if not img:
        manifest.append({'name': name, 'image': '', 'file': ''})
        print(f"{i+1:02d} {name}: NO IMAGE")
        continue
    url = img if img.startswith('http') else f"http://47.93.14.11{img}"
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'Host': '47.93.14.11'}), timeout=30).read()
        ext = 'jpg' if '.jpg' in url.lower() or 'jpeg' in url.lower() else ('png' if '.png' in url.lower() else 'img')
        fn = f"{i+1:02d}_{name.replace('/','_').replace(' ','_')}.{ext}"
        open(os.path.join(outdir, fn), 'wb').write(data)
        manifest.append({'name': name, 'image': img, 'file': fn})
        print(f"{i+1:02d} {name}: {len(data)}B -> {fn}")
    except Exception as e:
        manifest.append({'name': name, 'image': img, 'file': ''})
        print(f"{i+1:02d} {name}: FAIL {e}")
json.dump(manifest, open(os.path.join(outdir, '_manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved manifest', len(manifest))
