# -*- coding: utf-8 -*-
# 部署后端新闻模块修复（news_fetcher 关键词 + home 接口过滤），并重启后端服务
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FILES = [
    (r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\ai_engine\news_fetcher.py",
     "/www/wwwroot/yisu/backend/app/ai_engine/news_fetcher.py"),
    (r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend\app\api\home.py",
     "/www/wwwroot/yisu/backend/app/api/home.py"),
]

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)

def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')

# 备份 + 上传
sftp = cli.open_sftp()
for lp, rp in FILES:
    run("cp %s %s.bak_%s" % (rp, rp, os.path.basename(rp)))
    sftp.put(lp, rp)
    print("uploaded:", rp)
sftp.close()

# 语法检查
py = run("cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m py_compile app/ai_engine/news_fetcher.py app/api/home.py 2>&1")
print("compile:", (py or "OK").strip()[:300])

# 重启后端（venv uvicorn）
print(run("pkill -f 'uvicorn.*8765' 2>/dev/null; sleep 1; cd /www/wwwroot/yisu/backend && nohup 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 > /tmp/yisu_api.log 2>&1 & sleep 5; echo started").strip()[:200])
# 健康检查
print("health:", run("curl -s -m 8 http://127.0.0.1:8765/api/home/news?page_size=3 | head -c 600").strip()[:600])
cli.close()
print("=== DONE ===")
