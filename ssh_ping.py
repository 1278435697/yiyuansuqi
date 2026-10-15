# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
i, o, e = cli.exec_command("echo HELLO_TEST; hostname", timeout=30)
out = o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print("RESULT=[" + out + "]")
cli.close()
print("=== DONE ===")
