# -*- coding: utf-8 -*-
"""验证云数据库 fabrics 表（数量/清单）"""
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
SERVER_PY = '''# -*- coding: utf-8 -*-
import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='han050607',
                    database='yisu_ai', charset='utf8mb4')
cur = c.cursor()
cur.execute('SELECT COUNT(*) FROM fabrics')
print('COUNT=', cur.fetchone()[0])
cur.execute('SELECT id,name,category,dynasty_peak FROM fabrics ORDER BY id')
for r in cur.fetchall():
    print(r[0], '|', r[1], '|', r[2], '|', r[3])
cur.close(); c.close()
'''

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
with sftp.open('/tmp/check_fabrics.py', 'w') as f:
    f.write(SERVER_PY)
sftp.close()
i, o, e = cli.exec_command('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/check_fabrics.py', timeout=60)
out = o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print(out)
cli.close()
print('=== DONE ===')
