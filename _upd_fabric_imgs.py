# -*- coding: utf-8 -*-
"""更新新增8种面料 image_url"""
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
SERVER_PY = '''# -*- coding: utf-8 -*-
import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='han050607',
                    database='yisu_ai', charset='utf8mb4')
cur = c.cursor()
rows = [
    ('蜀锦', '/images/fabrics/fabric_shujin.jpg'),
    ('纨', '/images/fabrics/fabric_wan.jpg'),
    ('茧绸', '/images/fabrics/fabric_jianchou.jpg'),
    ('绸', '/images/fabrics/fabric_chou.jpg'),
    ('褐', '/images/fabrics/fabric_he.jpg'),
    ('蕉布', '/images/fabrics/fabric_jiaobu.jpg'),
    ('羽缎 / 羽纱', '/images/fabrics/fabric_yuduan.jpg'),
    ('库缎', '/images/fabrics/fabric_kuduan.jpg'),
]
for name, url in rows:
    cur.execute('UPDATE fabrics SET image_url=%s WHERE name=%s', (url, name))
    print('upd', name, cur.rowcount)
c.commit(); c.close()
'''

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
with sftp.open('/tmp/upd_imgs.py', 'w') as f:
    f.write(SERVER_PY)
sftp.close()
i, o, e = cli.exec_command('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/upd_imgs.py', timeout=60)
print(o.read().decode('utf-8', 'replace'))
print(e.read().decode('utf-8', 'replace')[:500])
cli.close()
print('=== DONE ===')
