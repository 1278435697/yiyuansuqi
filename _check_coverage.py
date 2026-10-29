import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("47.93.14.11", username="root", password="Han050607@")
cmd = (
    "mysql -uroot -phan050607 yisu_ai -e '"
    "SELECT COUNT(*) total, "
    "SUM(images IS NULL OR JSON_LENGTH(images)=0) no_img, "
    "SUM(dynasties IS NULL OR JSON_LENGTH(dynasties)=0) no_dyn, "
    "SUM(meanings IS NULL OR JSON_LENGTH(meanings)=0) no_meaning, "
    "SUM(props IS NULL OR JSON_LENGTH(props)=0 OR props=JSON_OBJECT()) no_props, "
    "SUM(pairs IS NULL OR JSON_LENGTH(pairs)=0) no_pairs, "
    "SUM(meaning IS NULL OR meaning=\"\") no_meaning_txt, "
    "SUM(applied IS NULL OR applied=\"\") no_applied "
    "FROM pattern_library;'"
)
stdin, stdout, stderr = c.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode()[-300:])
c.close()
