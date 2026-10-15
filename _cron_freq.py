# -*- coding: utf-8 -*-
"""cron 抓取频率 6h -> 2h，并立即触发一次抓取"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
# 替换 cron 行
cmd = r'''crontab -l | sed 's|0 \*/6 \* \* \* cd /www/wwwroot/yisu/backend.*news_fetcher.py.*|0 */2 * * * cd /www/wwwroot/yisu/backend \&\& /www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 app/ai_engine/news_fetcher.py >> /tmp/yisu_news_fetch.log 2>&1|' | crontab - && crontab -l | grep news_fetcher'''
_, out, err = cli.exec_command(cmd)
print(out.read().decode('utf-8','replace').strip())
cli.close()
print('=== DONE ===')
