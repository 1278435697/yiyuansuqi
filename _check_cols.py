import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = "mysql -uroot -phan050607 yisu_ai -e 'SHOW COLUMNS FROM fabrics LIKE \"craft\"; SHOW COLUMNS FROM fabrics LIKE \"poems\";' 2>/dev/null"
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
c.close()
