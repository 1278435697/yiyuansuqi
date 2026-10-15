# -*- coding: utf-8 -*-
# 云端导出 news 表：① mysqldump SQL 备份 ② python 生成 CSV（UTF-8-sig 供 Excel）
# 然后拉回本地
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL_DIR = r"C:\Users\lenovo\Desktop\yisu-ai-platform\backups"
os.makedirs(LOCAL_DIR, exist_ok=True)
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=300):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

# ① mysqldump
out = run("mysqldump -uroot -phan050607 --default-character-set=utf8mb4 yisu_ai news > /tmp/news_dump.sql 2>/tmp/dump_err.txt; echo DUMP_EXIT=$?; grep -v 'Warning' /tmp/dump_err.txt | head -3; wc -c /tmp/news_dump.sql")
print(out[:400])

# ② CSV（python 在云端生成）
py = (
 "import sys,logging,csv;logging.disable(logging.CRITICAL);sys.path.insert(0,'.');"
 "from sqlalchemy import text;from app.db.database import SessionLocal;"
 "db=SessionLocal();rows=db.execute(text('SELECT id,title,summary,source,source_url,dynasty_tags,entity_tags,cover_image,is_focus,publish_time,created_at,content FROM news ORDER BY id')).all();"
 "db.close();"
 "import io;"
 "f=open('/tmp/news_table.csv','w',newline='',encoding='utf-8-sig');w=csv.writer(f);"
 "w.writerow(['id','title','summary','source','source_url','dynasty_tags','entity_tags','cover_image','is_focus','publish_time','created_at','content']);"
 "[w.writerow([r.id,(r.title or '').replace('\\n',' '),(r.summary or '').replace('\\n',' '),r.source or '',r.source_url or '',r.dynasty_tags or '',r.entity_tags or '',r.cover_image or '',r.is_focus,str(r.publish_time or ''),str(r.created_at or ''),(r.content or '').replace('\\n',' ')]) for r in rows];"
 "f.close();print('CSV_ROWS=',len(rows))"
)
cmd = "cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -c \"" + py + "\" 2>&1"
print(run(cmd)[:300])

sftp = cli.open_sftp()
sftp.get("/tmp/news_dump.sql", os.path.join(LOCAL_DIR, "news_dump_20261014.sql"))
sftp.get("/tmp/news_table.csv", os.path.join(LOCAL_DIR, "news_table_20261014.csv"))
sftp.close()
for f in ["news_dump_20261014.sql", "news_table_20261014.csv"]:
    print("local:", f, os.path.getsize(os.path.join(LOCAL_DIR, f)))
cli.close()
print("=== DONE ===")
