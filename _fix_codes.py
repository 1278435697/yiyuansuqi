import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = (
    "mysql -uroot -phan050607 yisu_ai -e \""
    "SET @n := 320; "
    "UPDATE pattern_library SET code = (@n := @n + 1) WHERE code = 0 ORDER BY id; "
    "SELECT COUNT(*) AS zero_left, MAX(code) AS max_code FROM pattern_library;\" 2>/dev/null"
)
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
c.close()
