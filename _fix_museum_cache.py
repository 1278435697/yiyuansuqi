import paramiko
host="47.93.14.11"; user="root"; pw="Han050607@"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pw, timeout=30)
def run(cmd):
    stdin,stdout,stderr=ssh.exec_command(cmd, timeout=60)
    return stdout.read().decode('utf-8','ignore')+stderr.read().decode('utf-8','ignore')
CFG="/www/server/panel/vhost/nginx/yisu.conf"
print(run(f"cp {CFG} {CFG}.bak_20261018_nocache && echo BACKUP_OK"))
# 在 location = /museum/index.html 块后插入 museum assets no-cache 规则
inject = r'''    location = /museum/index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires -1;
    }

    # 博物馆子应用静态资源：内容变更时文件名不变（产物直改），必须协商缓存，避免旧版本残留
    location /museum/assets/ {
        add_header Cache-Control "no-cache";
        expires -1;
    }
'''
# 用 python 读改写配置（比 sed 可靠）
import io
data = run(f"cat {CFG}")
old_block = '''    location = /museum/index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires -1;
    }
'''
if old_block in data:
    new_data = data.replace(old_block, inject, 1)
    # 写回：用 sftp
    sftp = ssh.open_sftp()
    with sftp.open(CFG, "w") as f:
        f.write(new_data)
    sftp.close()
    print("INJECT_OK")
else:
    print("BLOCK_NOT_FOUND")
    print(data[data.find("museum"):data.find("museum")+800])
# nginx 测试与重载
print(run("nginx -t 2>&1"))
print(run("nginx -s reload 2>&1 || /etc/init.d/nginx reload 2>&1"))
print("=== 验证响应头 ===")
print(run("curl -sI http://127.0.0.1/museum/assets/index-DOlOnALt.js | head -8"))
ssh.close()
