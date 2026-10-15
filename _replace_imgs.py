# -*- coding: utf-8 -*-
"""下载4张替换图 → 覆盖本地 public → 上传服务器 dist"""
import urllib.request, io, sys, os, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IMGS = {
    'fabric_gebu.jpg':  'https://aka.doubaocdn.com/s/qwe2PRUldc',   # 草鞋山葛织品 国博
    'silk_juan.jpg':    'https://aka.doubaocdn.com/s/Be5jk7cNeI',   # 马山楚墓凤纹绣绢䋺衣
    'fabric_wan.jpg':   'https://aka.doubaocdn.com/s/sSiyUrhxSy',   # 生绢 白绢面
    'fabric_mianbu.jpg':'https://aka.doubaocdn.com/s/4f9HT79sbV',   # 松江布展柜文物
}
PUBLIC = r'C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\public\images\fabrics'
REMOTE_DIR = '/www/wwwroot/yisu/frontend/dist/images/fabrics'

# 1. 下载并覆盖本地
for fn, url in IMGS.items():
    data = urllib.request.urlopen(url, timeout=60).read()
    open(os.path.join(PUBLIC, fn), 'wb').write(data)
    print(f'local {fn}: {len(data)}B')

# 2. 上传服务器 dist
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
for fn in IMGS:
    sftp.put(os.path.join(PUBLIC, fn), f'{REMOTE_DIR}/{fn}')
sftp.close(); cli.close()
print('uploaded 4 files to server dist')
print('=== DONE ===')
