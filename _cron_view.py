# -*- coding: utf-8 -*-
"""修复 crontab：重写 news_fetcher 行为 2 小时一次"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
# 查看当前 crontab
_, out, err = cli.exec_command("crontab -l")
print("BEFORE:")
print(out.read().decode('utf-8','replace'))
cli.close()
print('=== DONE ===')
