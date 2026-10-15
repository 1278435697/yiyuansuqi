# -*- coding: utf-8 -*-
# ① 本地 news_fetcher.py/home.py 的 md5（与云端当前对比）
# ② 云端 .bak 是否含最新修复（publish_time=None / 摘要带正文）→ 判断 .bak 新旧
# ③ 云端当前文件关键行检查
import paramiko, io, sys, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''):
            h.update(c)
    return h.hexdigest()

base = r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend"
for rel in ["app/ai_engine/news_fetcher.py", "app/api/home.py"]:
    p = os.path.join(base, rel.replace("/", "\\"))
    print("LOCAL_MD5", rel, md5(p))

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
# .bak 是否含最新修复特征
out = run("cd /www/wwwroot/yisu/backend && grep -n 'publish_time=date or it\\[\"date\"\\] or None' app/ai_engine/news_fetcher.py.bak_news_fetcher.py; echo BAK_NF_ABOVE; grep -n 'publish_time=date or it\\[\"date\"\\] or None' app/ai_engine/news_fetcher.py; echo CUR_NF_ABOVE; grep -c 'body_ref' app/ai_engine/news_fetcher.py; echo CUR_BODYREF_COUNT; grep -c 'body_ref' app/ai_engine/news_fetcher.py.bak_news_fetcher.py; echo BAK_BODYREF_COUNT")
print(out[:1200])
cli.close()
print("=== DONE ===")
