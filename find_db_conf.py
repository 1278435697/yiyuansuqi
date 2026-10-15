# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=90):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
sql = r"""SELECT COUNT(*) FROM news WHERE
 source_url LIKE '%ds.163.com%' OR source_url LIKE '%chagushici%' OR source_url LIKE '%gushici.net%'
 OR source_url LIKE '%hanyuguoxue%' OR source_url LIKE '%wenku.baidu%' OR source_url LIKE '%zgbk.com%'
 OR source_url LIKE '%hm.com.cn%' OR source_url LIKE '%uniqlo%' OR source_url LIKE '%meikansocks%'
 OR source_url LIKE '%sheygo%' OR title LIKE '%怎么读%' OR title LIKE '%的意思%'
 OR title LIKE '%字典%' OR title LIKE '%词典%' OR title LIKE '%攻略%' OR title LIKE '%副本%'
 OR title LIKE '%拼音%' OR title LIKE '%读音%' OR title LIKE '%文库%' OR title LIKE '%古诗%';"""
# 找数据库连接信息
print(run("grep -n -A6 'SQLALCHEMY_DATABASE_URI\\|sqlalchemy.url\\|DATABASE_URL' /www/wwwroot/yisu/backend/app/core/config.py /www/wwwroot/yisu/backend/app/db/database.py 2>/dev/null | head -30")[:800])
cli.close()
print("=== DONE ===")
