# -*- coding: utf-8 -*-
"""同步 31 种面料档案到云数据库：UPDATE 现有23种 + INSERT 新增8种"""
import paramiko, io, sys, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '47.93.14.11'
PROFILES_JSON = r'C:\Users\lenovo\Desktop\yisu-ai-platform\_profiles_31.json'

profiles = json.load(open(PROFILES_JSON, encoding='utf-8'))

# html 名称 → 库内名称
NAME_MAP = {'兽皮': '兽皮毛皮'}

# 服务器端同步脚本（pymysql 参数化）
SERVER_PY = r'''# -*- coding: utf-8 -*-
import json, re, sys
import pymysql

profiles = json.load(open('/tmp/profiles31.json', encoding='utf-8'))
NAME_MAP = {'兽皮': '兽皮毛皮'}

def extract_book(text):
    m = re.search(r'《[^》]+》', text)
    return m.group(0) if m else ''

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='han050607',
                       database='yisu_ai', charset='utf8mb4')
cur = conn.cursor()
cur.execute('SELECT name FROM fabrics')
existing = {r[0] for r in cur.fetchall()}

updated = 0
inserted = 0
for p in profiles:
    db_name = NAME_MAP.get(p['name'], p['name'])
    cat = p['category']
    raw = p['raw_material']
    period = p['period']
    desc = p['description']
    if db_name in existing:
        cur.execute('UPDATE fabrics SET category=%s, raw_material=%s, dynasty_peak=%s, description=%s WHERE name=%s',
                    (cat, raw, period, desc, db_name))
        updated += cur.rowcount
    else:
        src_ref = extract_book(desc) or '史料见诗文检索'
        cur.execute('INSERT INTO fabrics (name, category, raw_material, dynasty_peak, technique, description, image_url, source_ref) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                    (p['name'], cat, raw, period, '', desc, '', src_ref))
        inserted += 1

conn.commit()
cur.execute('SELECT COUNT(*) FROM fabrics')
total = cur.fetchone()[0]
print('updated=%d inserted=%d total=%d' % (updated, inserted, total))
for r in cur.execute('SELECT id,name,category,dynasty_peak FROM fabrics ORDER BY id') or ():
    pass
cur.execute('SELECT id,name,category,dynasty_peak FROM fabrics ORDER BY id')
for r in cur.fetchall():
    print('  %s | %s | %s | %s' % r)
cur.close(); conn.close()
'''

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(HOST, port=22, username='root', password='Han050607@', timeout=25)

sftp = cli.open_sftp()
with sftp.open('/tmp/profiles31.json', 'w') as f:
    f.write(json.dumps(profiles, ensure_ascii=False))
with sftp.open('/tmp/sync_fabrics.py', 'w') as f:
    f.write(SERVER_PY)
sftp.close()

i, o, e = cli.exec_command('/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 /tmp/sync_fabrics.py', timeout=120)
out = o.read().decode('utf-8', 'replace')
err = e.read().decode('utf-8', 'replace')
print(out)
if err.strip():
    print('ERR:', err[:2000])
cli.close()
print('=== DONE ===')
