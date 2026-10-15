# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i, o, e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
# 查看当前 cron，然后改为每天 08:00 一次
print("--- crontab before ---")
print(run("crontab -l 2>&1 | grep -i news")[:500])
# 移除旧的每2小时任务，添加每天08:00任务（news_fetcher 权威源增量）
rm = run("crontab -l 2>/dev/null | grep -v 'news_fetcher' | crontab - ; crontab -l 2>/dev/null | cat")
print("--- after remove ---")
print(rm[:300])
add = run("( crontab -l 2>/dev/null | grep -v 'news_fetcher' ; echo '0 8 * * * cd /www/wwwroot/yisu/backend && 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 app/ai_engine/news_fetcher.py >> /tmp/yisu_news_fetch.log 2>&1' ) | crontab -")
print("--- add exit ---", add[:200])
print("--- crontab after ---")
print(run("crontab -l 2>&1 | grep -i news")[:500])
cli.close()
print("=== DONE ===")
