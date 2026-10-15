# -*- coding: utf-8 -*-
"""设置 crontab 定时抓取（每6小时）+ 验证手动触发接口"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
# 追加 cron：每6小时跑一次抓取
cron_cmd = (
    "(crontab -l 2>/dev/null | grep -v 'news_fetcher.py'; "
    "echo '0 */6 * * * cd /www/wwwroot/yisu/backend && /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 app/ai_engine/news_fetcher.py >> /tmp/yisu_news_fetch.log 2>&1') | crontab - "
)
_, out, err = cli.exec_command(cron_cmd)
out.read(); err.read()
_, out, err = cli.exec_command("crontab -l | grep news_fetcher")
print("CRON:", out.read().decode('utf-8','replace').strip())
cli.close()
print('=== DONE ===')
