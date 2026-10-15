# -*- coding: utf-8 -*-
# 检查云端关键文件现状 + .bak 备份版本对比（判断是否被我覆盖/是否有更新的云端版本）
import paramiko, io, sys, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
out = run("cd /www/wwwroot/yisu/backend && for f in app/ai_engine/news_fetcher.py app/api/home.py app/ai_engine/news_fetcher.py.bak_news_fetcher.py app/api/home.py.bak_home.py; do echo \"$f $(stat -c '%s %y' $f 2>/dev/null)\"; md5sum $f 2>/dev/null | cut -c1-32 | xargs echo \"  md5\"; done; echo ---; ls -la /www/wwwroot/yisu/backend/*.py")
print(out[:2500])

# 本地文件大小对照
for rel in ["app/ai_engine/news_fetcher.py", "app/api/home.py"]:
    p = os.path.join(r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend", rel.replace("/", "\\"))
    print("LOCAL", rel, os.path.getsize(p) if os.path.exists(p) else "MISSING")
cli.close()
print("=== DONE ===")
