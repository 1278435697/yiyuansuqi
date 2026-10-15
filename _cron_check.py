# -*- coding: utf-8 -*-
"""查 cron 状态 + 丝博列表页最新条目"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command("crontab -l 2>&1; echo '---'; date '+%Y-%m-%d %H:%M'; echo '---'; ls -la /www/wwwroot/yisu/backend/logs/ 2>/dev/null | tail -5")
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
