import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = "mysql -uroot -phan050607 yisu_ai -e 'SELECT id, name, created_by, JSON_EXTRACT(craft, \"$.history_note\") AS hn FROM fabrics WHERE id=77;'"
stdin, stdout, stderr = c.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
c.close()
