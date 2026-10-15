# -*- coding: utf-8 -*-
"""查看服务器后端 .env 大模型相关配置"""
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command("cat /www/wwwroot/yisu/backend/.env 2>/dev/null | grep -iE 'LLM|API|KEY|ark|volc|doubao|embed' ; echo '---'; ls /www/wwwroot/yisu/backend/.env 2>/dev/null")
print(out.read().decode('utf-8', 'replace'))
print(err.read().decode('utf-8', 'replace'))
cli.close()
