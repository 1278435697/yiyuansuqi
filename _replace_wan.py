# -*- coding: utf-8 -*-
"""纨替换为干净白绢生地图并上传"""
import urllib.request, io, sys, os, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
url = 'https://aka.doubaocdn.com/s/eSWvB6I0yy'  # 绢の白生地 白绢卷
fn = 'fabric_wan.jpg'
PUBLIC = r'C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\public\images\fabrics'
data = urllib.request.urlopen(url, timeout=60).read()
open(os.path.join(PUBLIC, fn), 'wb').write(data)
print(f'local {fn}: {len(data)}B')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
sftp.put(os.path.join(PUBLIC, fn), f'/www/wwwroot/yisu/frontend/dist/images/fabrics/{fn}')
sftp.close(); cli.close()
print('uploaded')
print('=== DONE ===')
